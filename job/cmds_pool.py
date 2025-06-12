import yaml
from pydantic import ValidationError
from logger import get_logger
from models.tasks_models import CMDS
from utils import format_object_for_log

logger = get_logger("main.cmds")


class CmdsCreate:
    def __init__(self, cmds_path):
        self.cmds = {}
        self.cmds_path = cmds_path
        self.refresh()

    def refresh(self):
        try:
            with open(self.cmds_path, "r", encoding="utf-8") as file:
                buffer = yaml.safe_load(file)
                for cmds_key in buffer:
                    cmds = buffer[cmds_key]
                    if cmds['activate']:
                        self.cmds[cmds_key] = CMDS(**cmds)
                        # output command info
                        logger.info(format_object_for_log(self.cmds[cmds_key]))
        except ValidationError as e:
            logger.error(e)


    def get_cmds(self):
        if len(self.cmds) == 0:
            logger.info("cmds queue is empty ,check it !")
            return None
        else:
            return self.cmds


CMDS_READER = CmdsCreate("cmds.yaml")


def get_cmds_all():
    CMDS_READER.get_cmds()
    return CMDS_READER