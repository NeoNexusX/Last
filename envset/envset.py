from dotenv import load_dotenv
import os

from logger import get_logger

logger = get_logger("env logger")
load_dotenv(".env")  # laod env file


class EnvSet:
    def __init__(self):
        self.env = load_dotenv(".env")
        if self.env:
            logger.info("loading environment variables sucessfully")
            logger.info(f"MAILGUN_DOMAIN :{os.getenv("MAILGUN_DOMAIN")}")
        else:
            logger.info("loading environment variables failed")
#ZVNRSW4QNAKVK66GAB6K4NNV