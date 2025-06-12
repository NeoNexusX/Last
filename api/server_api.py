"""
Server API module for managing server accounts and status.

This module provides functionality for:
- Server status monitoring
- Server account management
- Password updates
- Server connection testing
"""

import io
from datetime import datetime
from typing import Annotated, Dict, List, Optional, Union
from fastapi import HTTPException, Depends, status
from sqlmodel import select, Session
from starlette import status
from api.user_api import TokenDep
from database.db import SessionDep
from job.cmds_pool import get_cmds_all
from logger import get_logger
from models.server_models import (
    ServerPublic,
    DiskInfo,
    GPUInfo,
    ServerAccountDB,
    ServerAccountUpdate,
    ServerPublicList,
    ServerAccountPublic
)
from ssh.ssh_manager import get_ssh_connection, execute_commands

# Initialize logger
logger = get_logger("main.server_status")

server_account_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect server account name or password",
)

server_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="cant find any server info",
)

server_already_exists_exception = HTTPException(
    status_code=status.HTTP_409_CONFLICT,  # 409 Conflict
    detail="server already exists",  # 明确提示用户已存在
)

account_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect account name or password",
)
passwd_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="account password not changed,use new paaswd",
)

passwdnot_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="passwd not allow",
)

ssh_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="ssh failed,try again later , try to connet admin to change your server password",
)

sqlite_exception = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="sqlite error",
)

def format_bytes(bytes_str: str) -> str:
    """
    Format bytes into human-readable format.
    
    Args:
        bytes_str: String representation of bytes
        
    Returns:
        Formatted string with appropriate unit
    """
    try:
        bytes_val = int(bytes_str)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} PB"
    except Exception as e:
        logger.error(f"Error formatting bytes: {e}")
        return "Unknown"

async def get_server_status_linux(
    ip: str,
    username: str,
    password: str,
    port: int = 22
) -> ServerPublic:
    """
    Get server status information via SSH.
    
    Args:
        ip: Server IP address
        username: SSH username
        password: SSH password
        port: SSH port
        
    Returns:
        ServerPublic object containing server status information
        
    Raises:
        SSHConnectionException: If SSH connection fails
    """
    try:
        connection = await get_ssh_connection(ip, username, password, port)
        if not connection:
            # TODO :change
            logger.error(f"Cannot connect to {ip}:{port}")
            return ServerPublic(
                success=False,
                server_name="unknown",
                server_ip=ip,
                server_port=port
            )

        cmds = get_cmds_all()
        cmds.refresh()
        commands = cmds.get_cmds()['CMD_Server_Update']
        results = await execute_commands(connection, commands.cmds)

        # Process server information
        hostname = results.get("hostname", f"server-{ip.split('.')[-1]}").stdout.strip()
        cpu = results.get("cpu_info", "").stdout.strip()
        cpu_usage = float(results.get("cpu_usage", "-1").stdout.strip())
        cpucores = int(results.get("cpu_cores", "-1").stdout.strip())

        # Process memory information
        memory_values = results.get("memory_info", "0 0").stdout.split()
        memory_total = format_bytes(memory_values[0]) if memory_values else "0"
        memory_used = format_bytes(memory_values[1]) if len(memory_values) > 1 else "0"
        memory_usage = (int(memory_values[1]) / int(memory_values[0])) * 100 if len(memory_values) >= 2 else 0.0

        # Process disk information
        disks = []
        for line in results.get("disk_info", "").stdout.strip().splitlines():
            parts = line.strip().split()
            if len(parts) >= 4 and not any(x in parts[0] for x in ["tmpfs", "udev"]):
                disks.append(DiskInfo(
                    mount_point=parts[0],
                    total=format_bytes(parts[1]),
                    used=format_bytes(parts[2]),
                    usage=float(parts[3].replace('%', ''))
                ))

        # Process GPU information
        gpus = []
        gpu_data = results.get("gpu_info", "").stdout.strip()
        if gpu_data != "none":
            for line in gpu_data.splitlines():
                if ',' in line:
                    model, usage, mem_total, mem_used = map(str.strip, line.split(','))
                    gpus.append(GPUInfo(
                        model=model,
                        usage=float(usage),
                        memory_total=f"{mem_total} MB",
                        memory_used=f"{mem_used} MB"
                    ))

        return ServerPublic(
            success=True,
            server_name=hostname,
            account_name=username,
            server_ip=ip,
            server_port=port,
            hostname=hostname,
            cpu=cpu,
            cpucores=cpucores,
            cpu_usage=round(cpu_usage, 1),
            gpus=gpus,
            disks=disks,
            memory_total=memory_total,
            memory_used=memory_used,
            memory_usage=round(memory_usage, 1),
            last_updated=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error getting server status: {e}")
        raise ssh_exception

async def update_server_password_linux(
    ip: str,
    username: str,
    old_passwd: str,
    new_passwd: str,
    port: int = 22
) -> Dict[str, str]:
    """
    Update server user password via SSH.
    
    Args:
        ip: Server IP address
        username: SSH username
        old_passwd: Current password
        new_passwd: New password
        port: SSH port
        
    Returns:
        Dictionary containing operation status
        
    Raises:
        SSHConnectionException: If SSH connection or password update fails
    """
    try:
        cmds = get_cmds_all()
        cmds.refresh()
        commands = cmds.get_cmds()['CMD_Change_Code']
        input_values = [locals()[v] for v in commands.sequence.values()]
        input_stream = io.BytesIO('\n'.join(input_values).encode('utf-8'))

        connection = await get_ssh_connection(ip, username, old_passwd, port)
        if not connection:
            return {"status": "password is not right in our database, please update server information by admin"}

        result = await execute_commands(connection, commands.cmds, in_stream=input_stream)
        exit_code = result.get('change').exited
        stdout = result.get('change').stdout.lower()
        stderr = result['change'].stderr.lower()

        if exit_code == 0 and any(p in stdout for p in commands.flag.values()):
            logger.info(f"{username}: Successfully updated server password")
            return {"status": "success"}
        elif exit_code == 10:
            logger.error(f"{username}: Password is not allowed, {stderr}")
            return {"status": "password is not allowed"}

        return {"status": "failed"}
    
    except Exception as e:
        logger.error(f"Error updating server password: {e}")
        raise ssh_exception

async def test_server_linux(
    ip: str,
    username: str,
    password: str,
    port: int = 22
) -> Dict[str, str]:
    """
    Test server connection via SSH.
    
    Args:
        ip: Server IP address
        username: SSH username
        password: SSH password
        port: SSH port
        
    Returns:
        Dictionary containing test status
    """
    try:
        cmds = get_cmds_all()
        cmds.refresh()
        commands = cmds.get_cmds()['CMD_Test_Server']
        
        connection = await get_ssh_connection(ip, username, password, port)
        
        result = connection.run("echo 'Hello'", hide=True)
        return {"status": "success" if "Hello" in result.stdout else "failed"}
    except Exception as e:
        logger.error(f"Error testing server connection: {e}")
        return {"status": "failed"}

########################################################
# API
########################################################
async def get_user_server_info(
    user: TokenDep,
    session: SessionDep
) -> ServerPublicList:
    """
    Get all server information for a user.
    
    Args:
        user: User token dependency
        session: Database session dependency
        
    Returns:
        ServerPublicList containing all server information
        
    Raises:
        ServerAccountException: If no server accounts found
        ServerNotFoundException: If no servers found
    """
    try:
        stmt = select(ServerAccountDB).where(ServerAccountDB.username == user.username)
        accounts = session.exec(stmt).all()

        if not accounts:
            logger.error(f"User server info not found for {user.username}")
            raise account_exception

        server_list = []
        for account in accounts:
            status_data = await get_server_status_linux(
                ip=account.server_ip,
                username=account.account_name,
                password=account.account_password,
                port=account.server_port
            )
            server_list.append(status_data)

        if not server_list:
            logger.error(f"No servers found for {user.username}")
            raise server_exception()

        return ServerPublicList(servers=server_list)
    
    except Exception as e:
        logger.error(f"Error getting user server info: {e}")


async def update_user_server_info(user: TokenDep, server_new: ServerAccountUpdate, session: SessionDep):
    """
    Update user's server information including password change.
    
    Args:
        user: User token dependency
        server_new: New server account information
        session: Database session dependency
        
    Returns:
        dict: Status of the update operation and updated server account info
        
    Raises:
        HTTPException: Various exceptions for different error cases
    """
    # Validate password requirements
    if server_new.account_password == server_new.account_password_new:
        logger.error(f"Password change rejected for {user.username}: New password same as old password")
        raise passwd_exception
        
    if len(server_new.account_password_new) < 8:
        logger.error(f"Password change rejected for {user.username}: Password too short")
        raise passwdnot_exception

    try:
        # Find existing server account
        stmt = select(ServerAccountDB).where(
            ServerAccountDB.username == user.username,
            ServerAccountDB.account_password == server_new.account_password,
            ServerAccountDB.server_name == server_new.server_name
        )
        
        existing_server = session.exec(stmt).one_or_none()
        if not existing_server:
            logger.error(f"Server account not found for user {user.username}")
            raise server_account_exception

        # Update password on the server
        ssh_result = await update_server_password_linux(
            ip=existing_server.server_ip,
            username=existing_server.account_name,
            old_passwd=existing_server.account_password,
            new_passwd=server_new.account_password_new,
            port=existing_server.server_port
        )

        if ssh_result['status'] != "success":
            logger.error(f"Password update failed for user {user.username}: {ssh_result['status']}")
            return {
                'control_status': ssh_result['status'],
                'server_account': server_new
            }

        # Update database record
        server_new.account_password = server_new.account_password_new
        update_data = server_new.model_dump(exclude_unset=True)
        existing_server.sqlmodel_update(update_data)
        
        session.commit()
        session.refresh(existing_server)
        
        logger.info(f"Successfully updated server info for user {user.username}")
        
        return {
            'control_status': 'success',
            'server_account': server_new
        }
        
    except Exception as e:
        logger.error(f"Error in update_user_server_info for user {user.username}: {str(e)}")
        session.rollback()
        
        # Handle specific error types
        if "SSH" in str(e) or "Connection" in str(e):
            raise ssh_exception
        elif "database" in str(e) or "sql" in str(e):
            raise sqlite_exception
        else:
            raise server_account_exception


async def create_user_server(user: TokenDep, server: ServerAccountDB, session: SessionDep):
    """
    Create a new server account for a user.
    
    Args:
        user: User token dependency
        server: Server account information to create
        session: Database session dependency
        
    Returns:
        ServerAccountDB: Created server account
        
    Raises:
        HTTPException: Various exceptions for different error cases
    """
    try:
        # Check if server already exists
        stmt = select(ServerAccountDB).where(
            ServerAccountDB.username == user.username,
            server.server_ip == ServerAccountDB.server_ip,
            server.server_port == ServerAccountDB.server_port
        )
        existing_server = session.exec(stmt).first()
        
        if existing_server:
            logger.error(f"Server already exists for user {user.username} at {server.server_ip}:{server.server_port}")
            raise server_already_exists_exception
        
        # Test server connection before creating
        result = await test_server_linux(
            server.server_ip,
            server.account_name,
            server.account_password,
            port=server.server_port
        )
        
        if result['status'] != "success":
            logger.error(f"Failed to connect to server {server.server_ip} for user {user.username}")
            raise server_account_exception
            
        # Create server account in database
        session.add(server)
        session.commit()
        session.refresh(server)
        
        logger.info(f"Successfully created server account for user {user.username} at {server.server_ip}")
        return server
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error in create_user_server for user {user.username}: {str(e)}")
        
        # Handle specific error types
        if "already exists" in str(e):
            raise server_already_exists_exception
        elif "SSH" in str(e) or "Connection" in str(e):
            raise ssh_exception
        elif "database" in str(e) or "sql" in str(e):
            raise sqlite_exception
        else:
            raise server_account_exception


async def del_user_server(user: TokenDep, server: ServerAccountPublic, session: SessionDep):
    stmt = select(ServerAccountDB).where(ServerAccountDB.username == user.username,
                                         server.server_ip == ServerAccountDB.server_ip,
                                         server.server_name == ServerAccountDB.server_name)
    existing_server = session.execute(stmt).scalar_one_or_none()
    if existing_server is None:
        logger.error(f"server is not found for  existing")
        raise server_exception
    else:
        session.delete(existing_server)
        session.commit()
        logger.info(f"Successfully deleted server account for user {user.username}")
        return server


# FastAPI dependencies
ServerDep = Annotated[ServerPublicList, Depends(get_user_server_info)]
ServerAccountUpdater = Annotated[ServerAccountPublic, Depends(update_user_server_info)]
ServerAccountCreater = Annotated[ServerAccountPublic, Depends(create_user_server)]
ServerAccountdel = Annotated[ServerAccountPublic, Depends(del_user_server)]
