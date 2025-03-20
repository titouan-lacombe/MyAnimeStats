from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    allow_import: bool = False


config = AppConfig()
