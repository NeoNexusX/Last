import platform
from typing import Dict, List
from pydantic import BaseModel


# TODO : Combine CMDS and INTER_CMDS Together
class CMDS(BaseModel):
    platform: str
    cmds: Dict[str, str]
    activate: bool
    sequence : Dict[str, str] | None = None
    flag: Dict[str, str] |  None = None