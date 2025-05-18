import yaml
from pydantic import ValidationError
from logger import get_logger
from models.tasks_models import TASK, CMDS

logger = get_logger("main.task")

CLASS_MAP = {
    "task": TASK,
    "cmds": CMDS,
    
}

class TaskCreate:
    def __init__(self, tasks_path):
        self.task = {}
        self.cmds = {}
        self.tasks_path = tasks_path

    def read(self):
        try:
            with open(self.tasks_path, "r", encoding="utf-8") as file:
                buffer = yaml.safe_load(file)
                for task_key in buffer:
                    task = buffer[task_key]
                    if task['activate']:
                        task_type = task['type']
                        # get class obj dirctly from name
                        obj = getattr(self, task_type)
                        # set obj dict, only three types in the map
                        obj[task_key] = CLASS_MAP.get(task_type)(**task)

                        logger.info(
                            "API CMD data has been read in:\n" +
                            '\n'.join(f"{k}: {v}" for k, v in obj[task_key].__dict__.items())
                        )
        except ValidationError as e:
            logger.error(e)

    def get_cmds(self):
        return self.cmds

    def get_task(self):
        return self.task

    def get_all(self):
        if len(self.task) == 0 or len(self.cmds) == 0:
            self.read()
        else:
            logger.info("tasks queue is empty ,check it !")


TASKS_READER = TaskCreate("tasks.yaml")


def get_tasks():
    TASKS_READER.get_all()
    return TASKS_READER
