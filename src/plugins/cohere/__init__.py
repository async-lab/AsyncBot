from nonebot.plugin import PluginMetadata

from nonebot import get_plugin_config

from .cohere import *
from .config import Config

plugin_config = get_plugin_config(Config)

__plugin_meta__ = PluginMetadata(
    name="cohere",
    description="cohere",
    usage="cohere",
    type="application",
    config=Config,
    extra={},
)
