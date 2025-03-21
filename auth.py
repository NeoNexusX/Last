from datetime import timedelta, datetime, timezone
from typing import Annotated, Union
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError, ExpiredSignatureError
from passlib.context import CryptContext
from pydantic import BaseModel
from starlette import status
from database.db import SessionDep
from models.user_models import get_activate_user
import secrets
import jwt

SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect username or password",
    headers={"WWW-Authenticate": "Bearer"},
)

token_expired_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token expired",
    headers={"WWW-Authenticate": "Bearer"},
)

token_invalid_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid token",
    headers={"WWW-Authenticate": "Bearer"},
)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class FormData(BaseModel):
    username: str
    password: str
    model_config = {"extra": "forbid"}


def hashed_password(password: str) -> str:
    return PWD_CONTEXT.hash(password)


def verify_password(plain_pwd: str, hashed_pwd: str) -> bool:
    return PWD_CONTEXT.verify(plain_pwd, hashed_pwd)


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# 身份验证函数，依赖于get_activate_user
async def authenticate_user(username: str, password: str, db: SessionDep):
    user = await get_activate_user(username, db)
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_authenticated_user(
        username: str,
        password: str,
        db: SessionDep):
    user = await authenticate_user(username, password, db)
    if not user:
        raise credentials_exception
    return user


async def token_authen(token: Annotated[str, Depends(oauth2_scheme)], db: SessionDep):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise token_invalid_exception
        token_data = TokenData(username=username)

    except ExpiredSignatureError:
        raise token_expired_exception

    except InvalidTokenError:
        raise token_invalid_exception

    user = await get_activate_user(username, db)

    return user
