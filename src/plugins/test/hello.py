from nonebot import on_message
from nonebot.rule import Rule
from nonebot.adapters import Event
from nonebot.utils import logger_wrapper

log = logger_wrapper("test")


async def is_hello(event: Event) -> bool:
    return event.get_message() or event.get_message() == "hello"


rule = Rule(is_hello)

hello = on_message(rule=rule)


@hello.handle()
async def handler_hello():
    await hello.finish("Hello, AsyncLab!")
