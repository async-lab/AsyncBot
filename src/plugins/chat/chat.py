import requests
from nonebot import on_message, get_plugin_config, get_adapters
from nonebot.rule import Rule
from nonebot.params import EventMessage, Depends
from nonebot.typing import T_State
from nonebot.adapters import Event, Message
from nonebot.adapters.onebot.v11 import (
    PrivateMessageEvent,
    GroupMessageEvent,
    MessageEvent,
    Bot,
)
from nonebot.utils import logger_wrapper
import typing
from .api import Dify, BotMessage
from .config import plugin_config, Config

log = logger_wrapper("chat")


T = typing.TypeVar("T")


def retry(func: typing.Callable[[None], T]) -> T:
    error_times = 0

    while True:
        try:
            return func()
        except Exception as e:
            error_times += 1
            if error_times >= 3:
                log("ERROR", "Error occurred too many times. Cancelling...")
                return "回复超时。"
            else:
                log("ERROR", e)
                log("ERROR", "Error occurred. Retrying...")


dify = Dify(api_key=plugin_config.api_key)


async def rule_check(bot: Bot, event: MessageEvent):
    if event.message_type == "group":
        return event.is_tome()
    else:
        return any(
            friend["user_id"] == event.sender.user_id
            for friend in await bot.get_friend_list()
        )


on_message_matcher = on_message(rule=Rule(rule_check))


@on_message_matcher.handle()
async def handler(event: MessageEvent = Depends(lambda event: event)) -> None:
    session_id = event.get_session_id()
    plain_message = event.get_message().extract_plain_text()

    if plain_message == "清除历史":
        dify.histories[session_id] = []
        await on_message_matcher.send("历史已清除。")
        return

    message = f"User: [{event.get_user_id()}]; Message: [{plain_message}]"

    response = retry(
        lambda: dify.chat(
            message=message,
            session_id=session_id,
        )
    )
    await on_message_matcher.send(response)

    return
