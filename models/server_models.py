import random
from typing import Annotated
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, select

from auth import token_authen
from database.db import SessionDep
from models.user_models import UserInDB


class ServerPublic(BaseModel):
    name: str
    cpu: str
    cpu_usage: float
    gpu: str
    gpu_usage: float
    disk: str
    disk_usage: float


class ServerAccountBase(SQLModel):
    username: str = Field(default=None, primary_key=True, foreign_key="userindb.username")
    server_name: str = Field(default=None, primary_key=True)
    account_name: str = Field()
    server_ip: str = Field()


class ServerAccountDB(ServerAccountBase, table=True):
    account_password: str = Field()


# 检查用户的对应的服务器内容
async def get_user_server_info(
        user: Annotated[UserInDB, Depends(token_authen)],
        session: SessionDep):
    # try:
    # 查询数据库获取账户信息
    stmt = select(ServerAccountDB).where(ServerAccountDB.username == user.username)
    accounts = session.exec(stmt).all()

    if not accounts:
        return {"servers": []}

    server_list = []
    for account in accounts:
        print(account)
        try:
            # 获取实时服务器状态
            status_data = await get_server_status(account.server_ip)

            # 合并数据结构
            server_info = {
                "server_name": account.server_name,
                "account_name": account.account_name,
                "server_ip": account.server_ip,
                "status": status_data.model_dump()
            }
            server_list.append(server_info)
        except Exception as status_error:
            # 记录错误但继续处理其他服务器
            print(f"Failed to get status for {account.server_ip}: {str(status_error)}")

    return {"servers": server_list}


# except Exception as e:
#     raise HTTPException(status_code=500, detail="internal server error") from e


async def get_server_status(ip: str) -> ServerPublic:
    try:
        # 示例1：本地模拟数据
        return ServerPublic(
            name=f"server-{ip.split('.')[-1]}",
            cpu="Intel Xeon Gold 6238R",
            cpu_usage=round(random.uniform(5, 80), 1),
            gpu="NVIDIA A100",
            gpu_usage=round(random.uniform(10, 90), 1),
            disk="2TB NVMe SSD",
            disk_usage=round(random.uniform(10, 95), 1)
        )

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"无法获取服务器 {ip} 状态: {str(e)}"
        )


ServerDep = Annotated[Session, Depends(get_user_server_info)]
