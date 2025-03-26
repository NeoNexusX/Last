from datetime import datetime
from typing import List
from pydantic import BaseModel
from sqlmodel import Field, SQLModel


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
    server_name: str | None = None
    account_name: str | None = None
    server_ip: str | None = None
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


class ServerPublicList(BaseModel):
    servers: List[ServerPublic]


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
