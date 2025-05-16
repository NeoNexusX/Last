import io
from datetime import datetime
from typing import Annotated
from fastapi import HTTPException, Depends
from sqlmodel import select
from starlette import status
from api.user_api import TokenDep
from database.db import SessionDep
from logger import get_logger
from models.server_models import ServerPublic, DiskInfo, GPUInfo, \
    ServerAccountDB, ServerAccountUpdate, ServerPublicList, ServerAccountPublic
from ssh.ssh_manager import get_ssh_connection, execute_commands
from task.task_pool import get_tasks

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


def _format_bytes(bytes_str: str) -> str:
    try:
        bytes_val = int(bytes_str)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} PB"
    except Exception as e:
        logger.error(e)
        return "Unknown"


#########################
# Util
#########################
# TODO：optimize the function and fix result return
async def get_server_status_linux(ip: str,
                                  username: str,
                                  password: str, port=22) -> ServerPublic:
    connection = await get_ssh_connection(ip, username, password, port)

    if not connection:
        logger.error(f"cannot connect to {ip}:{port}")
        return ServerPublic(success=False,
                            server_name="unknown",
                            server_ip=ip,
                            server_port=port)

    commands = get_tasks().get_cmds()['CMD_Server_Update']

    results = await execute_commands(connection, commands.cmds)

    # get hostname
    hostname = results.get("hostname", f"server-{ip.split('.')[-1]}").stdout.strip()

    # deal cpu info
    cpu = results.get("cpu_info", "").stdout.strip()

    # get cpu usage
    cpu_usage_str = results.get("cpu_usage", "-1").stdout.strip()
    try:
        cpu_usage = float(cpu_usage_str)
    except ValueError:
        cpu_usage = -1

    cpucores = int(results.get("cpu_cores", "-1").stdout.strip())

    # get memory info
    memory_values = results.get("memory_info", "0 0").stdout.split()
    memory_total = _format_bytes(memory_values[0]) if len(memory_values) > 0 else "0"
    memory_used = _format_bytes(memory_values[1]) if len(memory_values) > 1 else "0"
    memory_usage = (int(memory_values[1]) / int(memory_values[0])) * 100 if len(memory_values) >= 2 else 0.0

    # get disk usage
    disks = []
    for line in results.get("disk_info", "").stdout.strip().splitlines():
        parts = line.strip().split()
        if len(parts) >= 4 and not any(x in parts[0] for x in ["tmpfs", "udev"]):
            disks.append(DiskInfo(
                mount_point=parts[0],
                total=_format_bytes(parts[1]),
                used=_format_bytes(parts[2]),
                usage=float(parts[3].replace('%', ''))
            ))

    # get gpu info
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


async def update_server_password_linux(ip: str,
                                       username: str,
                                       old_passwd: str,
                                       new_passwd: str,
                                       port=22) -> dict[str, str]:
    """
    Update server user password via SSH

    Args:
        :param port: host ip port
        :param ip: host ip
        :param username: host username
        :param old_passwd: Current password
        :param new_passwd: New password

    Returns:
        Operation result dictionary
    """

    # Password update method (interactive)
    commands = get_tasks().get_cmds()['CMD_Change_Code']

    input_values = [locals()[v] for v in commands.sequence.values()]


    # create a stream
    input_stream = io.BytesIO(
        '\n'.join(input_values).encode('utf-8')
    )
    # Run password change command
    connection = await get_ssh_connection(ip, username, old_passwd, port)

    if not connection:
        return {"status": f"password is not right in our database, please update server information by admin"}

    result = await execute_commands(
        connection,
        commands.cmds,
        in_stream=input_stream
    )

    exit_code = result.get('change').exited
    stdout = result.get('change').stdout.lower()
    stderr = result['change'].stderr.lower()

    # Check success indicators
    if exit_code == 0 and any(p in stdout for p in commands.flag.values()):
        logger.info(f"{username} : Successfully updated server password")
        return {"status": "success"}
    elif exit_code == 10:
        logger.error(f"{username} : password is not allowed,{stderr}")
        return {"status": f"password is not allowed"}

    return {"status": "failed"}


async def test_server_linux(ip: str, username: str, password: str, port=22):
    connection = await get_ssh_connection(ip, username, password, port)
    if not connection:
        return {"status": "failed"}
    result = connection.run("echo 'Hello'", hide=True)
    if "Hello" in result.stdout:
        return {"status": "success"}
    else:
        return {"status": "failed"}


#########################
# API
#########################
# find users server info
async def get_user_server_info(user: TokenDep, session: SessionDep) -> ServerPublicList:
    # find user database information
    stmt = select(ServerAccountDB).where(ServerAccountDB.username == user.username)
    accounts = session.exec(stmt).all()

    if not accounts:
        logger.error(f"User server info not found.")
        raise account_exception

    server_list = []
    for account in accounts:
        # get server information
        status_data = await get_server_status_linux(
            ip=account.server_ip,
            username=account.account_name,
            password=account.account_password,
            port=account.server_port
        )
        server_list.append(status_data)

    if not server_list:
        logger.error(f"No servers found for {user.username}")
        raise server_exception

    return ServerPublicList(servers=server_list)


async def update_user_server_info(user: TokenDep, server_new: ServerAccountUpdate, session: SessionDep):
    # test for passwd
    if server_new.account_password == server_new.account_password_new:
        logger.error(f"Password change for {user.username} is same")
        raise passwd_exception
    elif len(server_new.account_password_new) < 8:
        logger.error(f"Password change for {user.username} is too short")
        raise passwdnot_exception

    # find user database information
    stmt = select(ServerAccountDB).where(
        ServerAccountDB.username == user.username,
        ServerAccountDB.account_password == server_new.account_password,
        ServerAccountDB.server_name == server_new.server_name
    )
    result = session.execute(stmt)
    existing_server = result.scalar_one_or_none()

    # If no existing server found, raise an exception
    if existing_server is None:
        logger.error(f"No servers found for {user.username}")
        raise server_account_exception

    ssh_result = await update_server_password_linux(
        ip=existing_server.server_ip,
        username=existing_server.account_name,
        old_passwd=existing_server.account_password,
        new_passwd=server_new.account_password_new,
        port=existing_server.server_port
    )

    if ssh_result['status'] == "success":
        # update model
        server_new.account_password = server_new.account_password_new
        update_data = server_new.model_dump(exclude_unset=True)
        existing_server.sqlmodel_update(update_data)

        #  update sqlite
        session.commit()
        session.refresh(existing_server)

    return {'control_status': ssh_result['status'],
            'server_account': server_new}


async def create_user_server(user: TokenDep, server: ServerAccountDB, session: SessionDep):
    stmt = select(ServerAccountDB).where(ServerAccountDB.username == user.username,
                                         server.server_ip == ServerAccountDB.server_ip,
                                         server.server_port == ServerAccountDB.server_port)
    existing_server = session.execute(stmt).scalar_one_or_none()
    if existing_server is None:
        result = await test_server_linux(server.server_ip, server.account_name, server.account_password,
                                         port=server.server_port)
        if result['status'] == "success":
            session.add(server)
            session.commit()
            session.refresh(server)
        else:
            logger.error(f"servers acccount is not right")
            raise server_account_exception

    else:
        logger.error(f"servers found for exit")
        raise server_already_exists_exception

    return server


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
        return server


ServerDep = Annotated[ServerPublicList, Depends(get_user_server_info)]
ServerAccountUpdater = Annotated[ServerAccountPublic, Depends(update_user_server_info)]
ServerAccountCreater = Annotated[ServerAccountPublic, Depends(create_user_server)]
ServerAccountdel = Annotated[ServerAccountPublic, Depends(del_user_server)]
