import typing
from enum import Enum


class AIMessage:
    class Role(Enum):
        USER = "user"
        ASSISTANT = "assistant"
        SYSTEM = "system"

    def __init__(self, role: Role, content: str):
        self.role = role
        self.content = content


class Bot:

    role_map: typing.Dict[AIMessage.Role, str] = {
        member: member.value for member in AIMessage.Role
    }

    def __init__(self, api_key: str, model: str = None, max_tokens: int = 1024):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens

    def message_to_dict(self, message: AIMessage) -> typing.Dict:
        return {"role": self.role_map[message.role], "content": message.content}

    def chat(
        self,
        message: str,
        preamble: str = "",
        stream=False,
        history: typing.Iterable[AIMessage] = [],
        reply_start_handler: typing.Callable[[], None] = lambda: None,
        reply_message_handler: typing.Callable[[str], None] = lambda: None,
        reply_end_handler: typing.Callable[[], None] = lambda: None,
    ) -> str:
        pass
