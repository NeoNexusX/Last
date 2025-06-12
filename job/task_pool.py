import yaml
from pydantic import ValidationError
from job.cmds_pool import get_cmds_all
from logger import get_logger
from models.tasks_models import TASK, CMDS
from utils import format_object_for_log

logger = get_logger("main.task")


class TaskCreate:
    def __init__(self, tasks_path):
        self.task = {}
        self.tasks_path = tasks_path
        self.refresh()

    def refresh(self):
        cmds = get_cmds_all()
        cmds.refresh()
        cmds_list = cmds.get_cmds()
        try:
            with open(self.tasks_path, "r", encoding="utf-8") as file:
                buffer = yaml.safe_load(file)
                for task_key in buffer:
                    task = buffer[task_key]
                    if task['activate']:
                        task['tasks'] = [cmds_list[cmd] for cmd in task['tasks']]
                        self.task[task_key] = TASK(**task)
                        # output task info
                        logger.info(format_object_for_log(self.task[task_key]))
        except KeyError as e:
            logger.error(f"Task {task_key} is not found in tasks.yaml")
        except ValidationError as e:
            logger.error(e)


    def get_task(self):
        if len(self.task) == 0:
            logger.info("tasks queue is empty ,check it !")
            return None
        else:
            return self.task


TASKS_READER = TaskCreate("tasks.yaml")


def get_tasks_all():
    TASKS_READER.get_task()
    return TASKS_READER
