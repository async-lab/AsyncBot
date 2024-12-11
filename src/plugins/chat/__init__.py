from nonebot.plugin import PluginMetadata
from .chat import *
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="chat",
    description="chat",
    usage="chat",
    type="application",
    config=Config,
    extra={},
)
