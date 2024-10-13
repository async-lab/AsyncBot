import requests
from nonebot import on_message, get_plugin_config
from nonebot.rule import Rule
from nonebot.params import EventMessage, Depends
from nonebot.typing import T_State
from nonebot.adapters import Event, Message
from nonebot.adapters.onebot.v11 import (
    PrivateMessageEvent,
    GroupMessageEvent,
    MessageEvent,
)
from nonebot.utils import logger_wrapper
import typing
from .ai.api import AIMessage
from .ai.models import Cohere
from .config import Config

log = logger_wrapper("cohere")

plugin_config = get_plugin_config(Config)
bot = Cohere(api_key=plugin_config.cohere_api_key)
history: typing.Mapping[str, typing.List[AIMessage]] = {}
history_max_len = 20

preamble = ""


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


def get_uptime() -> str:
    url = plugin_config.uptime_url
    api_key = plugin_config.uptime_api_key
    response = requests.get(
        url=url, auth=("", api_key), headers={"User-Agent": "curl/7.64.1"}
    )
    if response.status_code != 200:
        return "error"

    metrics = response.text
    monitor_status_lines = [
        line for line in metrics.splitlines() if line.startswith("monitor_status")
    ]

    return monitor_status_lines


def get_mc() -> str:
    url = plugin_config.mc_url
    response = requests.get(url=url, headers={"User-Agent": "curl/7.64.1"})
    if response.status_code != 200:
        return "error"

    return response.text


async def is_group(event: GroupMessageEvent):
    return True


on_message_matcher = on_message(rule=Rule(is_group))


@on_message_matcher.handle()
async def handler(event: MessageEvent = Depends(lambda event: event)):
    session_id = event.get_session_id()
    plain_message = event.get_message().extract_plain_text()

    final_message = f"User: [{event.get_user_id()}]; Message: [{plain_message}]"

    if session_id not in history:
        history[session_id] = []

    if event.is_tome():
        if "uptime" in plain_message:
            final_message = f"{final_message}; Uptime: [{get_uptime()}]"
        elif "mc" in plain_message:
            final_message = f"{final_message}; MC: [{get_mc()}]"

        response = retry(
            lambda: bot.chat(
                message=final_message,
                preamble=preamble,
                history=history[session_id],
            )
        )
        history[session_id].append(AIMessage(AIMessage.Role.USER, final_message))
        history[session_id].append(AIMessage(AIMessage.Role.ASSISTANT, response))
        await on_message_matcher.send(response)
    else:
        history[session_id].append(AIMessage(AIMessage.Role.USER, final_message))

    while len(history[session_id]) > history_max_len:
        history[session_id].pop(0)
