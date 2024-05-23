from .db import Db
from khl import Bot


class Context:
    pass


class ContextProgram(Context):
    def __init__(self) -> None:
        self.bot: Bot = None
        self.db: Db = None
        self.token = None


program: ContextProgram = ContextProgram()


def init_program(bot: Bot, db: Db, token: str) -> None:
    global program
    program.bot = bot
    program.db = db
    program.token = token
    program.db.create_table(
        "candidate",
        {
            "user_id": "TEXT",
            "name": "TEXT",
            "url": "TEXT",
            "description": "TEXT",
        },
    )
    program.db.create_table(
        "vote",
        {
            "multi": "INTEGER",
            "end": "TEXT",
            "msg_id": "TEXT",
        },
    )
    program.db.create_table(
        "vote_counting",
        {
            "user_id": "TEXT",
            "candidate_id": "TEXT",
            "vote_id": "TEXT",
        },
    )
