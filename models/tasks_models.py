from typing import Dict
from pydantic import BaseModel
from logger import get_logger

logger = get_logger("main.task_models")


# TODO : Combine CMDS and INTER_CMDS Together
class CMDS(BaseModel):
    cmds: Dict[str, str]
    type: str
    activate: bool


class INTER_CMDS(CMDS):
    sequence: Dict[str, str]
    flag: Dict[str, str]


class TASK(CMDS):
    cycle: str
    trigger: str


# task group to deal with a series of tasks
class TASKS(BaseModel):
    task: TASK
