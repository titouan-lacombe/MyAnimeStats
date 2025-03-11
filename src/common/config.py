from os import getenv
from pydantic import BaseModel


class Config(BaseModel):
    @classmethod
    def from_env(cls, **overrides):
        build_args = {}

        for key in cls.model_fields.keys():
            if key in overrides:
                build_args[key] = overrides[key]
                continue

            env_val = getenv(key.upper())
            if env_val is not None:
                build_args[key] = env_val

        return cls(**build_args)


class AppConfig(Config):
    allow_import: bool = False


config = AppConfig.from_env()
