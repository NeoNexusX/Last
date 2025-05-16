from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from logger import get_logger
from task.task_pool import get_tasks

logger = get_logger("main.task_scheduler")

SCHEDULER = BackgroundScheduler()

# TODO：Task 统一执行函数
def task_handler(task_name,type,platform):
    logger.info(f"Task {task_name} is running")
    get_tasks()

    logger.error(f"Task {task_name} type is not supported")

# TODO：定时任务触发