from pydantic import BaseModel, field_validator, Field
from nonebot import get_plugin_config


class Config(BaseModel):
    api_key: str = Field(..., alias="API_KEY")


plugin_config = get_plugin_config(Config)
