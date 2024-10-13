import typing
import cohere
from .api import Bot, AIMessage


class Cohere(Bot):

    role_map = {
        AIMessage.Role.USER: "USER",
        AIMessage.Role.ASSISTANT: "CHATBOT",
    }

    def __init__(
        self,
        api_key: str,
        model: str = "command-r-plus-08-2024",
        max_tokens: int = 512,
    ) -> None:
        super().__init__(api_key=api_key, model=model, max_tokens=max_tokens),
        self.client = cohere.Client(api_key=api_key)

    def message_to_dict(self, message: AIMessage) -> typing.Dict:
        return {
            "role": self.role_map[message.role],
            "text": message.content,
        }

    def chat(
        self,
        message: str,
        preamble: str = "",
        history: typing.Iterable[AIMessage] = [],
    ) -> str:
        total = self.client.chat(
            message=message,
            preamble=preamble,
            model=self.model,
            max_tokens=self.max_tokens,
            chat_history=[self.message_to_dict(m) for m in history],
        ).text
        return total
