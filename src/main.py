import os
import asyncio
from khl import Bot
from base.db import Db
from base.logger import logger
from base.context import init_program, program
from base.handler import init_handlers


async def main():
    token = os.environ.get("KOOK_TOKEN")
    db_path = os.environ.get("DB_PATH")
    channel_id = os.environ.get("CHANNEL_ID")
    if not token:
        logger.error("Kook token is missing")
        token = input("Enter your kook token: ")
    if not db_path:
        logger.error("Db path is missing")
        db_path = input("Enter your db path: ")
    if not channel_id:
        logger.error("Channel id is missing")
        channel_id = input("Enter your channel id: ")
    db = Db(path=db_path)
    bot = Bot(token=token)
    init_program(db=db, bot=bot, token=token, channel_id=channel_id)
    init_handlers()
    task = asyncio.create_task(bot.start())
    done, pending = await asyncio.wait({task})


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
