from typing import Annotated
from fastapi import Depends, HTTPException
from sqlmodel import Field, SQLModel, select
from database.db import SessionDep


class UserBase(SQLModel):
    username: str = Field()
    active: bool = Field(default=False)


class UserInDB(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    email: str = Field()
    password: str = Field()
    hashed_password: str = Field()
    # token: str = Field(default=None)


class UserPublic(UserBase):
    email: str


class UserCreate(UserBase):
    email: str
    password: str


class UserUpdate(UserBase):
    email: str = Field(default=None)
    password: str | None = None


# 获取用户基础函数
async def get_user(username: str, db: SessionDep):
    # 通过 Session 查询用户
    statement = select(UserInDB).where(UserInDB.username == username)
    return db.exec(statement).first()


# 检查用户是否激活的函数
async def get_activate_user(username: str, db: SessionDep) -> UserInDB:
    user = await get_user(username, db)
    if not user:
        raise HTTPException(status_code=400, detail="User is not exists")
    if not user.active:
        raise HTTPException(status_code=400, detail="User is not active")
    return user


UserDep = Annotated[UserInDB, Depends(get_activate_user)]
