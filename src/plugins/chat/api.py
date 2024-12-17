import typing
import requests
import json
import os
from enum import Enum
from .config import plugin_config, Config


class BotMessage:
    class Role(Enum):
        USER = "user"
        ASSISTANT = "assistant"
        SYSTEM = "system"

    def __init__(self, role: Role, content: str):
        self.role = role
        self.content = content


class Dify:
    role_map = {
        BotMessage.Role.USER: "USER",
        BotMessage.Role.ASSISTANT: "CHATBOT",
    }

    histories: typing.Mapping[str, typing.List[BotMessage]] = {}
    history_max_tokens = 2560

    def __init__(self, api_key: str, base_url="https://api.dify.ai"):
        self.api_key = api_key
        self.base_url = base_url

    def message_to_dict(self, message: BotMessage) -> typing.Dict:
        return {
            "role": self.role_map[message.role],
            "text": message.content,
        }

    def chat(
        self,
        message: str,
        session_id: str,
    ) -> str:
        if session_id not in self.histories:
            self.histories[session_id] = []
        while (
            sum(len(m.content.encode("utf-8")) for m in self.histories[session_id])
            > self.history_max_tokens
        ):
            self.histories[session_id].pop(0)

        response = requests.post(
            url=f"{self.base_url}/v1/workflows/run",
            headers={"Authorization": "Bearer " + self.api_key},
            json={
                "inputs": {
                    "message": message,
                    "history": json.dumps(
                        [
                            self.message_to_dict(m)
                            for m in self.histories.get(session_id, [])
                        ]
                    ),
                },
                "response_mode": "blocking",
                "user": "AsyncBot",
            },
            proxies={
                "http": os.environ.get("http_proxy"),
                "https": os.environ.get("https_proxy"),
            },
        )

        if response.status_code != 200:
            return f"Error {response.status_code}: {response.text}"

        reply = response.json()["data"]["outputs"]["text"]

        self.histories[session_id].append(BotMessage(BotMessage.Role.USER, message))
        self.histories[session_id].append(BotMessage(BotMessage.Role.ASSISTANT, reply))
        return reply
