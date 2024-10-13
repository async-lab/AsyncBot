from pydantic import BaseModel, field_validator


class Config(BaseModel):
    cohere_api_key: str
    uptime_url: str
    uptime_api_key: str
    mc_url: str
