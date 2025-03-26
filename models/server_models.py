from datetime import datetime
from typing import Annotated, List
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, select
from starlette import status

from api.userapi import TokenDep
from database.db import SessionDep
from logger import get_logger
from ssh.ssh_manager import get_ssh_connection, execute_commands
import io

# 获取服务器状态模块的日志器
logger = get_logger("main.server_status")

server_account_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect server account name or password",
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


#########################
# MODELS
#########################
class HardwareUsage(BaseModel):
    name: str
    usage: float


class GPUInfo(BaseModel):
    model: str
    usage: float
    memory_total: str
    memory_used: str


class DiskInfo(BaseModel):
    mount_point: str
    total: str
    used: str
    usage: float


class ServerPublic(BaseModel):
    success: bool
    server_port: int = 22
    message: str | None = None
    hostname: str | None = None
    cpu: str | None = None
    cpucores: int | None = None
    cpu_usage: float | None = None
    gpus: List[GPUInfo] | None = None
    disks: List[DiskInfo] | None = None
    memory_total: str | None = None
    memory_used: str | None = None
    memory_usage: float | None = None
    last_updated: datetime | None = None


class ServerAccountBase(SQLModel):
    username: str = Field(default=None, primary_key=True, foreign_key="userindb.username")
    server_name: str = Field(default=None, primary_key=True)
    account_name: str = Field()
    server_ip: str = Field()
    server_port: int = Field(default=22)


class ServerAccountDB(ServerAccountBase, table=True):
    account_password: str = Field()


class ServerAccountUpdate(ServerAccountBase):
    account_password: str = Field()
    account_password_new: str


class ServerAccountPublic(ServerAccountBase):
    account_password: str = Field()


#########################
# Util
#########################

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


async def get_server_status_linux(ip: str,
                                  username: str,
                                  password: str, port=22) -> ServerPublic:
    try:
        connection = await get_ssh_connection(ip, username, password, port)

        if not connection:
            raise server_account_exception

        commands = {
            "hostname": "hostname | cut -d'.' -f1",
            "cpu_info": """if grep -q 'model name' /proc/cpuinfo; then
                                grep -m 1 'model name' /proc/cpuinfo | awk -F': ' '{print $2}'
                            elif grep -q 'Hardware' /proc/cpuinfo; then
                                grep -m 1 'Hardware' /proc/cpuinfo | awk -F': ' '{print $2}'
                            else
                                echo "cpu unknow"
                            fi
                            """,
            "cpu_usage": "top -b -n1 | grep -F 'Cpu(s)' | awk -v RS=',' '/id/{gsub(\"%id\",\"\",$0); print 100 - $1}'",
            "cpu_cores": "nproc",
            "memory_info": "free -b | awk '/Mem:/ {print $2,$3}'",
            "disk_info": "df -B1 --output=target,size,used,pcent | tail -n +2",
            "gpu_check": "which nvidia-smi && nvidia-smi --query-gpu=name,utilization.gpu,memory.total,memory.used --format=csv,noheader,nounits || echo 'none'"
        }

        results = await execute_commands(connection, commands)

        # get hostname
        hostname = results.get("hostname", f"server-{ip.split('.')[-1]}").strip()

        # deal cpu info
        cpu = results.get("cpu_info", "")

        # get cpu usage
        cpu_usage_str = results.get("cpu_usage", "0").strip()
        try:
            cpu_usage = float(cpu_usage_str)
        except ValueError:
            cpu_usage = -1

        cpucores = int(results.get("cpu_cores", "-1").strip())

        # get memory info
        memory_values = results.get("memory_info", "0 0").split()
        memory_total = _format_bytes(memory_values[0]) if len(memory_values) > 0 else "0"
        memory_used = _format_bytes(memory_values[1]) if len(memory_values) > 1 else "0"
        memory_usage = (int(memory_values[1]) / int(memory_values[0])) * 100 if len(memory_values) >= 2 else 0.0

        # get disk usage
        disks = []
        for line in results.get("disk_info", "").splitlines():
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
        gpu_data = results.get("gpu_check", "")
        if gpu_data != "none":
            for line in gpu_data.splitlines():
                if ',' in line:
                    model, usage, mem_total, mem_used = map(str.strip, line.split(','))
                    gpus.append(GPUInfo(
                        model=model,
                        usage=float(usage),
                        memory_total=f"{mem_total} MiB",
                        memory_used=f"{mem_used} MiB"
                    ))

        return ServerPublic(
            success=True,
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

    except HTTPException as e:
        logger.error(f"Failed to connect to server: {ip}, error: {e}")
        return ServerPublic(success=False,
                            message="account is not right")

    except Exception as e:
        logger.error(f"Failed to connect to server: {ip}, error: {e}")
        return ServerPublic(success=False,
                            message="somthing went wrong,try again later")


async def update_server_password_linux(ip: str,
                                       username: str,
                                       old_password: str,
                                       new_password: str,
                                       port=22) -> dict[str, str]:
    """
    Update server user password via SSH

    Args:
        :param port: host ip port
        :param ip: host ip
        :param username: host username
        :param old_password: Current password
        :param new_password: New password

    Returns:
        Operation result dictionary
    """
    # Password update method (interactive)
    # Password update method (interactive)
    password_change_method = {
        "command": "passwd",
        "input_sequence": [
            old_password + "\n",  # Current password
            new_password + "\n",  # New password
            new_password + "\n"  # Confirm new password
        ],
        "success_indicators": [
            "successfully",
            "password updated",
            "passwd: password updated successfully"
        ]
    }

    try:
        # 创建一个字节流，模拟交互输入
        input_stream = io.BytesIO(
            ''.join(password_change_method["input_sequence"]).encode('utf-8')
        )
        # Run password change command
        connection = await get_ssh_connection(ip, username, old_password, port)

        if not connection:
            raise ConnectionError("Failed to connect to server")

        result = connection.run(
            password_change_method["command"],
            in_stream=input_stream,  # 使用字节流
            hide=True,
            timeout=10,  # 10秒超时
        )

        exit_code = result.exited
        stdout = result.stdout.lower()
        stderr = result.stderr.lower()

        # Check success indicators
        success_phrases = ["successfully", "changing"]
        if exit_code == 0 and any(p in stdout for p in success_phrases):
            return {"status": "success"}
        elif exit_code == 10:
            return {"status": f"password is not allowed,{stderr}"}

        return {"status": f"failed"}

    except ConnectionError as e:
        logger.error(f"Failed to connect to server: {ip}, error: {e}")
        raise

    except Exception as e:
        logger.error(f"SSH password update error: {str(e)}")
        return {"status": f"failed"}


#########################
# API
#########################

# 获取服务器状态的函数


# find users server info
async def get_user_server_info(user: TokenDep,
                               session: SessionDep):
    try:
        # find user database information
        stmt = select(ServerAccountDB).where(ServerAccountDB.username == user.username)
        accounts = session.exec(stmt).all()

        if not accounts:
            raise account_exception

        server_list = []
        for account in accounts:
            try:
                # get server information
                status_data = await get_server_status_linux(
                    ip=account.server_ip,
                    username=account.account_name,
                    password=account.account_password,
                    port=account.server_port
                )
                server_info = {
                    "server_name": account.server_name,
                    "account_name": account.account_name,
                    "server_ip": account.server_ip
                }
                server_info.update({"status": status_data.model_dump()})
                server_list.append(server_info)

            except Exception as status_error:
                # save error , keep deal with other server
                logger.error(f"Failed to get status for {account.server_ip}: {str(status_error)}")

        return {"servers": server_list}

    except HTTPException as e:
        logger.error(f"account not find {user.username}: {e}")
        return {"servers": []}

    except Exception as e:
        logger.error(f"Abnormal exception ,{user.username} happen in : {e}")
        raise


async def update_user_server_info(user: TokenDep,
                                  server_new: ServerAccountUpdate,
                                  session: SessionDep):
    try:
        if server_new.account_password == server_new.account_password_new:
            raise passwd_exception
        elif len(server_new.account_password_new) < 8:
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
            raise server_account_exception

        ssh_result = await update_server_password_linux(
            ip=existing_server.server_ip,
            username=existing_server.account_name,
            old_password=existing_server.account_password,
            new_password=server_new.account_password_new,
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

    except HTTPException as e:
        logger.error(f"account not find {user.username}: {e}")
        raise

    except ConnectionError:
        raise ssh_exception


async def del_user_server(user: TokenDep, session: Session):
    pass


ServerDep = Annotated[Session, Depends(get_user_server_info)]
ServerAccountUpdater = Annotated[ServerPublic, Depends(update_user_server_info)]
