from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Annotated
from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordRequestForm
from auth import credentials_exception, ACCESS_TOKEN_EXPIRE_MINUTES, \
    create_access_token, Token, token_authen, get_authenticated_user, hashed_password
from database.db import create_db_and_tables, SessionDep
from models.server_models import ServerDep
from models.user_models import UserInDB, UserPublic, UserCreate, UserUpdate
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    create_db_and_tables()
    yield
    # 关闭时执行（可选清理逻辑）

app = FastAPI(lifespan=lifespan)

origins = ["*", ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: SessionDep) -> Token:
    user = await get_authenticated_user(form_data.username, form_data.password, db)
    if not user:
        raise credentials_exception
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

    return Token(access_token=access_token, token_type="bearer")


@app.get("/usr", response_model=UserPublic)
async def get_current_usr(user: Annotated[UserInDB, Depends(token_authen)]):
    return user


@app.post("/signup", response_model=UserPublic)
async def create_user(user: UserCreate, session: SessionDep):
    user = UserInDB(**user.model_dump(), hashed_password=hashed_password(user.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.post("/change", response_model=UserPublic)
async def update_user(user: UserUpdate, user_past: Annotated[UserInDB, Depends(token_authen)], session: SessionDep):
    user_data = user.model_dump(exclude_unset=True)
    user_past.sqlmodel_update(user_data)
    session.add(user_past)
    session.commit()
    session.refresh(user_past)
    return user


@app.delete("/del")
async def del_user(user: Annotated[UserInDB, Depends(token_authen)], session: SessionDep):
    session.delete(user)
    session.commit()
    return {"del": True}


@app.get("/server")
async def update_sever(server: ServerDep):
    return server
