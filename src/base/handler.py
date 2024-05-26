from khl import Bot, EventTypes, MessageTypes, Message, PublicMessage, Event, Channel
from khl.card import Card, CardMessage, Module, Types, Element, Struct
from .context import program
from .logger import logger
from datetime import datetime, timedelta
import aiohttp
import traceback
import json


def init_handlers():

    def channel_filter(message: Message) -> bool:
        return (
            isinstance(message, PublicMessage)
            and message.channel.id == program.channel_id
        )

    async def is_admin(message: Message) -> bool:
        if not isinstance(message, PublicMessage):
            return False
        return any(
            [
                r.id in message.author.roles and r.permissions & 0x1 == 0x1
                for r in (await message.ctx.guild.fetch_roles())
            ]
        )

    async def make_request(
        method: str,
        endpoint: str,
        headers: dict = {},
        data: str = None,
    ):
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=f"https://www.kookapp.cn/api/v3{endpoint}",
                headers={"Authorization": f"Bot {program.token}", **headers},
                data=data,
            ) as response:
                if response.status != 200:
                    logger.error(f"An error occurred: {response.status}")
                    logger.error(await response.json())
                return await response.json()

    async def update_message(msg_id: str, content: str):
        return await make_request(
            method="POST",
            endpoint="/message/update",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"msg_id": msg_id, "content": content}),
        )

    async def update_vote():
        votes = program.db.select("vote")
        if len(votes) == 0:
            return
        if int(datetime.now().timestamp()) > int(votes[0]["end"]):
            return
        await update_message(
            msg_id=votes[0]["msg_id"], content=json.dumps(await get_vote_message())
        )

    async def delete_message(msg_id: str):
        return await make_request(
            method="POST",
            endpoint="/message/delete",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"msg_id": msg_id}),
        )

    async def get_vote_message():
        votes = program.db.select("vote")
        if len(votes) == 0:
            return
        vote = votes[0]
        end = datetime.fromtimestamp(int(vote["end"]))
        c = Card()
        if int(datetime.now().timestamp()) > int(vote["end"]):
            c.append(Module.Header("投票已结束"))
        else:
            c.append(
                Module.Countdown(
                    end=datetime.fromtimestamp(int(vote["end"])),
                    mode=Types.CountdownMode.HOUR,
                )
            )
        candidates = program.db.select("candidate")
        if len(candidates) != 0:
            c.append(Module.Divider())
            c.append(Module.Header("不可多选" if vote["multi"] == 0 else "可多选"))
            for candidate in candidates:
                c.append(Module.Divider())
                vote_count = len(
                    program.db.select(
                        table_name="vote_counting",
                        condition=f"candidate_id='{candidate['id']}'",
                    )
                )
                c.append(
                    Module.Section(
                        Element.Text(
                            f"**id**: {candidate['id']}\n**用户**:{(await program.bot.fetch_user(candidate['user_id'])).nickname}\n**名称**: {candidate['name']}\n**链接**: {candidate['url']}\n**描述**: {candidate['description']}\n"
                        ),
                        Element.Button(
                            text=f"投票 目前票数={vote_count}",
                            click=Types.Click.RETURN_VAL,
                            theme=Types.Theme.PRIMARY,
                            value=f"{candidate['id']}",
                        ),
                    )
                )
        return CardMessage(c)

    @program.bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
    async def on_click(b: Bot, e: Event):
        msg_id = e.body["msg_id"]
        user_id = e.body["user_id"]
        candidate_id = e.body["value"]
        votes = program.db.select("vote")
        if len(votes) == 0:
            return
        vote = votes[0]
        if msg_id != vote["msg_id"]:
            return
        if int(datetime.now().timestamp()) > int(vote["end"]):
            return

        channel = await program.bot.fetch_public_channel(e.body["target_id"])

        if (
            len(
                program.db.select(
                    table_name="vote_counting",
                    condition=f"user_id='{user_id}' and candidate_id='{candidate_id}'",
                )
            )
            > 0
        ):
            program.db.delete(
                table_name="vote_counting",
                condition=f"user_id='{user_id}' and candidate_id='{candidate_id}'",
            )
            await update_vote()
            return

        if vote["multi"] == 0:
            program.db.delete(
                "vote_counting",
                f"user_id='{user_id}'",
            )

        program.db.insert(
            "vote_counting",
            {
                "user_id": user_id,
                "candidate_id": candidate_id,
                "vote_id": vote["id"],
            },
        )
        await update_vote()

    @program.bot.command(regex="^用法(?!\S).*")
    async def usage(message: PublicMessage):
        if not channel_filter(message):
            return
        await message.reply(
            """
用法：

添加 名称 链接 描述 --> 添加一个选项
查看 --> 查看所有选项
删除 id --> 删除一个选项
投票 --> 打开投票页面
"""
        )

    @program.bot.command(regex="^添加(?!\S).*")
    async def add_candidate(message: PublicMessage):
        if not channel_filter(message):
            return

        params = message.content.split()
        if len(params) < 4:
            await message.reply("参数错误")
            return
        program.db.insert(
            "candidate",
            {
                "user_id": message.author.id,
                "name": params[1],
                "url": params[2],
                "description": ", ".join(params[3:]),
            },
        )
        await message.reply(f"已添加 {params[1]}")

        await update_vote()

    @program.bot.command(regex="^查看(?!\S).*")
    async def show_candidates(message: PublicMessage):
        if not channel_filter(message):
            return

        candidates = program.db.select("candidate")
        if len(candidates) == 0:
            await message.reply("没有选项")
        else:
            c = Card()
            c.append(Module.Header("选项列表"))
            for candidate in candidates:
                c.append(Module.Divider())
                c.append(
                    Module.Section(
                        Element.Text(
                            f"**id**: {candidate['id']}\n**用户**:{(await program.bot.fetch_user(candidate['user_id'])).nickname}\n**名称**: {candidate['name']}\n**链接**: {candidate['url']}\n**描述**: {candidate['description']}\n"
                        )
                    )
                )
            await message.reply(CardMessage(c))

    @program.bot.command(regex="^删除(?!\S).*")
    async def delete_candidate(message: PublicMessage):
        if not channel_filter(message):
            return
        params = message.content.split()
        if len(params) != 2:
            await message.reply("参数错误(?!\S)")
            return
        candidates = program.db.select("candidate", condition=f"id='{params[1]}'")
        if len(candidates) == 0:
            await message.reply(f"没有找到选项：{params[1]}")
        for candidate in candidates:
            if candidate["user_id"] == message.author.id or not await is_admin(message):
                program.db.delete("candidate", f"id='{params[1]}'")
                program.db.delete("vote_counting", f"candidate_id='{params[1]}'")
                await message.reply(f"删除成功：{params[1]}")
            else:
                await message.reply(f"没有权限：{params[1]}")

        await update_vote()

    @program.bot.command(regex="^投票(?!\S).*")
    async def vote(message: PublicMessage):
        if not channel_filter(message):
            return
        votes = program.db.select("vote")
        if len(votes) == 0:
            await message.reply("没有投票")
            return
        if int(datetime.now().timestamp()) > int(votes[0]["end"]):
            await message.reply("投票已结束")
            return
        candidates = program.db.select("candidate")
        if len(candidates) == 0:
            await message.reply("没有选项")
            return
        await delete_message(votes[0]["msg_id"])
        res = await program.bot.send(
            target=message.channel, content=await get_vote_message()
        )
        program.db.update("vote", {"msg_id": res["msg_id"]}, "1=1")

    @program.bot.command(regex="^删除所有(?!\S).*")
    async def delete_candidates(message: PublicMessage):
        if not channel_filter(message):
            return
        if not await is_admin(message):
            await message.reply("没有权限")
            return
        program.db.delete("candidate", "1=1")
        await message.reply("删除成功")
        await update_vote()

    @program.bot.command(regex="^启动投票(?!\S).*")
    async def start_voting(message: PublicMessage):
        if not channel_filter(message):
            return
        if not await is_admin(message):
            await message.reply("没有权限")
            return

        params = message.content.split()
        if len(params) != 3:
            await message.reply("参数错误")
            return
        try:
            days = int(params[1])
            multi = int(params[2])
        except ValueError:
            await message.reply("参数错误")
            return
        votes = program.db.select("vote")
        if len(votes) > 0 and int(datetime.now().timestamp()) < int(votes[0]["end"]):
            await delete_message(votes[0]["msg_id"])
        program.db.delete("vote", "1=1")
        program.db.delete("vote_counting", "1=1")
        end = int(datetime.now().timestamp()) + int(days * 86400)
        program.db.insert("vote", {"multi": multi, "end": end, "msg_id": None})
        res = await program.bot.send(
            target=message.channel, content=await get_vote_message()
        )
        program.db.update("vote", {"msg_id": res["msg_id"]}, "1=1")
        await message.reply(f"投票已启动，将在{days}天后结束")

    @program.bot.command(regex="^结束投票(?!\S).*")
    async def end_voting(message: PublicMessage):
        if not channel_filter(message):
            return
        if not await is_admin(message):
            await message.reply("没有权限")
            return
        votes = program.db.select("vote", columns=["msg_id"])
        if len(votes) == 0:
            await message.reply("没有投票")
            return
        program.db.update("vote", {"end": "0"}, "1=1")
        await update_message(
            msg_id=votes[0]["msg_id"], content=json.dumps(await get_vote_message())
        )
        program.db.delete("vote", "1=1")
        await message.reply("投票已结束")
