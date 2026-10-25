#!/usr/bin/env python3
"""/history: the last 10 finished tasks of the user."""
from html import escape
from time import time

from pyrogram.filters import command
from pyrogram.handlers import MessageHandler

from bot import bot, user_data
from bot.helper.ext_utils.bot_utils import (
    get_readable_file_size,
    get_readable_time,
    new_task,
)
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import auto_delete_message, sendMessage


@new_task
async def history(_, message):
    user = message.from_user
    tasks = user_data.get(user.id, {}).get("history") or []
    if not tasks:
        reply = await sendMessage(message, "<i>No finished tasks yet!</i>")
        return await auto_delete_message(message, reply)
    lines = []
    for no, task in enumerate(tasks, start=1):
        name = escape(task.get("name", ""))
        if link := task.get("link"):
            name = f"<a href='{link}'>{name}</a>"
        ago = get_readable_time(time() - task.get("time", time()))
        lines.append(
            f"<b>{no}.</b> {name}\n┊ <b>Size:</b> {get_readable_file_size(task.get('size', 0))}"
            f" | <b>Mode:</b> {task.get('mode', '')}\n╰ <b>Done:</b> {ago} ago"
        )
    text = f"㊂ <b><u>History of {escape(user.first_name or str(user.id))} :</u></b>\n\n"
    text += "<blockquote expandable>" + "\n\n".join(lines) + "</blockquote>"
    buttons = ButtonMaker()
    buttons.ibutton("Cʟᴏsᴇ", f"wzmlx {user.id} close")
    await sendMessage(message, text, buttons.build_menu(1))


bot.add_handler(
    MessageHandler(
        history,
        filters=command(BotCommands.HistoryCommand)
        & CustomFilters.authorized
        & ~CustomFilters.blacklisted,
    )
)
