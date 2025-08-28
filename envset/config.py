import yaml
from logger import get_logger
from pydantic import ValidationError
from models.config_models import Config

logger = get_logger("main.settings")


class ConfigCreate:

    def __init__(self):
        super().__init__()
        self.config = None
        self.read()

    def read(self):
        try:
            with open("config.yaml", "r") as file:
                self.config = Config(**yaml.safe_load(file))
                logger.info(f"config data has read in \n" +
                            '\n'.join(f"{k}: {v}" for k, v in self.config))

        except ValidationError as e:
            logger.error(e)
        except Exception as e:
            logger.error(e)

    def get_config(self):
        if self.config is None:
            logger.error("config file not found")
        return self.config


CONFIG = ConfigCreate()


def get_config():
    return CONFIG.get_config()
