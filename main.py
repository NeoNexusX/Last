import os
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import Depends, FastAPI

from api.serverapi import ServerDep, ServerAccountUpdater, ServerAccountCreater, ServerAccountdel
from api.userapi import UserLoginDep, token_authen, UserCreateDep, UserUpdateDep, UserDeleDep
from models.auth import Token
from database.db import create_db_and_tables
from logger import logger_manager, get_logger
from models.server_models import ServerAccountPublic

from models.user_models import UserInDB, UserPublic
from fastapi.middleware.cors import CORSMiddleware
from ssh.ssh_manager import ssh_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    create_db_and_tables()
    yield
    # 关闭时执行（可选清理逻辑）
    await ssh_manager.close_all_connections()


app = FastAPI(lifespan=lifespan)

LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

# 初始化日志管理器
logger_manager.init_app(
    app=app,
    log_level=LOG_LEVEL,
    log_dir=os.getenv("LOG_DIR", "logs")
)

# 获取应用主日志器
logger = get_logger("main")

origins = ["*", ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.delete("/server_delete",response_model=ServerAccountPublic)
async def update_server_account(server: ServerAccountdel):
    return server
