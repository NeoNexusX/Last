import platform
from typing import Dict, List
from pydantic import BaseModel
from logger import get_logger

logger = get_logger("main.task_models")


# TODO : Combine CMDS and INTER_CMDS Together
class CMDS(BaseModel):
    platform: str
    cmds: Dict[str, str]
    type: str
    activate: bool
    sequence : Dict[str, str] | None = None
    flag: Dict[str, str] |  None = None

# task group to deal with a series of cmds
class TASK(BaseModel):
    platform: str
    type: str
    cycle: str
    trigger: str
    tasks: List[str]
    activate: bool


# {
#   "username": "neo",
#   "server_name": "Bionet_No1",
#   "account_name": "Neo",
#   "server_ip": "10.26.58.61",
#   "server_port": 22,
#   "account_password": "neo660789",
#   "account_password_new": "zhuzeyu6678"
# }