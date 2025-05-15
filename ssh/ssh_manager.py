from typing import Dict, Annotated
from fastapi import Depends
import asyncio
from fabric import Connection, Result
from logger import get_logger
from types import SimpleNamespace

empty_result = SimpleNamespace(
    stdout="",
    stderr="",
    exited=1,      # 非 0 表示失败
    ok=False,
    failed=True,
    command=""
)

# logger for ssh
logger = get_logger("main.ssh")


# ssh connection pool
class SSHConnectionManager:
    def __init__(self):
        self.connections: Dict[str, Connection] = {}
        self.locks: Dict[str, asyncio.Lock] = {}

    async def get_connection(self, ip: str, username: str, password: str, port=22) -> Connection | None:
        """create or reuse ssh connection"""
        connection_key = f"{username}@{ip}"

        # if connection doesn't have a lock, create a lock
        if connection_key not in self.locks:
            self.locks[connection_key] = asyncio.Lock()

        # use lock to make sure thread safe
        async with self.locks[connection_key]:
            # connet if exist keep it
            if connection_key in self.connections:
                conn = self.connections[connection_key]
                try:
                    # test connect alive
                    transport = conn.client.get_transport()
                    if transport and transport.is_active():
                        return conn
                    else:
                        # connect is inactive recreation
                        logger.info(f"Connection {connection_key} is inactive, recreating")
                except Exception as e:
                    logger.warning(f"Error checking connection {connection_key}: {str(e)}")

            # create a new connecting
            try:
                logger.info(f"Creating new SSH connection to {connection_key}")
                connection = Connection(
                    host=ip,
                    user=username,
                    port=port,
                    connect_kwargs={
                        "password": password,
                        "look_for_keys": False,
                    },
                    connect_timeout=5
                )
                connection.config.run.env = {
                    'LANG': 'en_US.UTF-8',
                    'LC_ALL': 'en_US.UTF-8',
                    'LANGUAGE': 'en_US'
                }
                # test connect
                connection.run("echo 'Testing connection'", hide=True)
                self.connections[connection_key] = connection
                return connection

            except Exception as e:
                logger.error(f"Failed to create new SSH connection to {connection_key}: {str(e)}")
                return None

    async def close_connection(self, ip: str, username: str, port=22):
        """close specific SSH connection"""
        connection_key = f"{username}@{ip} -p {port}"
        if connection_key in self.connections:
            try:
                self.connections[connection_key].close()
                del self.connections[connection_key]
                logger.info(f"Closed SSH connection to {connection_key}")
            except Exception as e:
                logger.error(f"Error closing connection to {connection_key}: {str(e)}")

    async def close_all_connections(self):
        """close all ssh connections"""
        for key, connection in list(self.connections.items()):
            try:
                connection.close()
                logger.info(f"Closed SSH connection to {key}")
            except Exception as e:
                logger.error(f"Error closing connection to {key}: {str(e)}")
                raise
        self.connections.clear()


# create one ssh_manager
ssh_manager = SSHConnectionManager()


# dep function
async def get_ssh_connection(ip: str, username: str, password: str, port=22) -> Connection:
    return await ssh_manager.get_connection(ip, username, password, port)


# batch to run execute_commands
async def execute_commands(connection: Connection, commands: Dict[str, str], in_stream=None) -> Dict[str, Result]:
    """
    Args:
        :param connection: SSH connection
        :param commands: command dicts，{name: commands str}
        :param in_stream:
    Returns:
        Dict[str, str]: results
    """
    results = {}

    for name, cmd in commands.items():
        result = empty_result
        try:
            result = connection.run(cmd,
                                    in_stream=in_stream,
                                    hide=True,
                                    warn=True,
                                    timeout=10)
        except Exception as e:
            logger.error(f"Error executing command: {name}: {str(e)}")

        results[name] = result
    return results


# create Depend
SSHConnectionDep = Annotated[Connection, Depends(get_ssh_connection)]
