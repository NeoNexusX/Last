import uvicorn
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.email_api import EmailConfirmDep, EmailConfirmSMTPDep
from api.server_api import ServerDep, ServerAccountUpdater, ServerAccountCreater, ServerAccountdel
from api.user_api import UserLoginDep, token_authen, UserCreateDep, UserUpdateDep, UserDeleDep
from database.db import create_db_and_tables
from envset.config import get_config
from envset.envset import EnvSet
from logger import get_logger
from models.auth import Token
from models.email_models import EmailConfirmRequest
from models.server_models import ServerAccountPublic
from models.user_models import UserInDB, UserPublic
from ssh.ssh_manager import ssh_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # start run
    create_db_and_tables()
    EnvSet()
    yield
    # close run
    await ssh_manager.close_all_connections()


app = FastAPI(lifespan=lifespan)

# get the main logger
logger = get_logger("main")

# get config
config = get_config()

# CORSMiddleware
origins = ["*", ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


#########################
# API
#########################

@app.post("/login")
async def login(token: UserLoginDep) -> Token:
    try:
        return token
    except Exception as e:
        raise e


@app.get("/user", response_model=UserPublic)
async def get_current_usr(user: Annotated[UserInDB, Depends(token_authen)]):
    return user


@app.post("/signup", response_model=UserPublic)
async def create_user(user: UserCreateDep):
    return user


@app.post("/change", response_model=UserPublic)
async def update_user(user: UserUpdateDep):
    return user


@app.delete("/del")
async def del_user(user: UserDeleDep):
    return user


@app.get("/server")
async def update_sever(server: ServerDep):
    return server


@app.post("/server_update")
async def update_server_account(server: ServerAccountUpdater):
    return server


@app.post("/server_create", response_model=ServerAccountPublic)
async def create_user_server(server: ServerAccountCreater):
    return server


@app.delete("/server_delete", response_model=ServerAccountPublic)
async def update_server_account(server: ServerAccountdel):
    return server


@app.post("/emailrequest", response_model=EmailConfirmRequest)
async def create_user_server(email: EmailConfirmDep):
    return email


@app.post("/emailsmtprequest", response_model=EmailConfirmRequest)
async def create_user_server(email: EmailConfirmSMTPDep):
    return email


# 新增：Uvicorn 启动配置
if __name__ == "__main__":
    uvicorn.run(
        "main:app",  # 模块名:FastAPI 实例名
        host=config.server.host,  # 监听所有网络接口
        port=config.server.port,  # 端口号
        log_level=config.server.log_level,  # 日志级别
        reload=True,  # 开发时自动重载
    )
