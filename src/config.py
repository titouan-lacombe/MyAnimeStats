import logging
from os import getenv

from pydantic import BaseModel

logger = logging.getLogger(__name__)

KB = 1000
MB = 1000 * KB
GB = 1000 * MB


class Config(BaseModel):
    @classmethod
    def from_env(cls):
        env_args = {}
        for key in cls.model_fields:
            env_val = getenv(key.upper())
            if env_val is not None:
                env_args[key] = env_val
        return cls(**env_args)
