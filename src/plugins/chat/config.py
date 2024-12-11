from pydantic import BaseModel, field_validator
from nonebot import get_plugin_config


class Config(BaseModel):
    api_key: str


plugin_config = get_plugin_config(Config)
