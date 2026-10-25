#!/usr/bin/env python3
from asyncio import sleep
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex

from bot import download_dict, bot, bot_name, download_dict_lock, OWNER_ID, user_data
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    deleteMessage,
    auto_delete_message,
    editMessage,
    editReplyMarkup,
)
from bot.helper.ext_utils.bot_utils import (
    getDownloadByGid,
    getAllDownload,
    MirrorStatus,
    new_task,
    multi_tags,
    retry_tasks,
)
from bot.helper.telegram_helper import button_build


async def cancel_mirror(_, message):
    user_id = message.from_user.id
    msg = message.text.split("_", maxsplit=1)
    if len(msg) > 1:
        cmd_data = msg[1].split("@", maxsplit=1)
        if len(cmd_data) > 1 and cmd_data[1].strip() != bot_name:
            return
        gid = cmd_data[0]
        dl = await getDownloadByGid(gid)
        if dl is None:
            await sendMessage(message, f"GID: <code>{gid}</code> Not Found.")
            return
    elif reply_to_id := message.reply_to_message_id:
        async with download_dict_lock:
            dl = download_dict.get(reply_to_id, None)
        if dl is None:
            await sendMessage(message, "This is not an active task!")
            return
    elif len(msg) == 1:
        msg = (
            "Reply to an active Command message which was used to start the download"
            f" or send <code>/{BotCommands.CancelMirror}_GID</code> to cancel it!"
        )
        await sendMessage(message, msg)
        return
    if (
        OWNER_ID != user_id
        and dl.message.from_user.id != user_id
        and (user_id not in user_data or not user_data[user_id].get("is_sudo"))
    ):
        await sendMessage(message, "This task is not for you!")
        return
    obj = dl.download()
    await obj.cancel_download()


async def cancel_all(status, user_id=None):
    matches = await getAllDownload(status, user_id)
    if not matches:
        return False
    for dl in matches:
        obj = dl.download()
        await obj.cancel_download()
        await sleep(1)
    return True


def _is_sudo(user_id):
    return user_id == OWNER_ID or user_data.get(user_id, {}).get("is_sudo")


def cancel_all_menu(owner_id, scope):
    """scope 0 = all tasks of the bot (sudo), else only that user's tasks."""
    buttons = button_build.ButtonMaker()
    for label, status in [
        ("Downloading", MirrorStatus.STATUS_DOWNLOADING),
        ("Uploading", MirrorStatus.STATUS_UPLOADING),
        ("Seeding", MirrorStatus.STATUS_SEEDING),
        ("Cloning", MirrorStatus.STATUS_CLONING),
        ("Extracting", MirrorStatus.STATUS_EXTRACTING),
        ("Archiving", MirrorStatus.STATUS_ARCHIVING),
        ("QueuedDl", MirrorStatus.STATUS_QUEUEDL),
        ("QueuedUp", MirrorStatus.STATUS_QUEUEUP),
        ("Paused", MirrorStatus.STATUS_PAUSED),
        ("All", "all"),
    ]:
        buttons.ibutton(label, f"canall {owner_id} {scope} {status}")
    if _is_sudo(owner_id):
        if scope:
            buttons.ibutton("🌐 All Tasks", f"canall {owner_id} scope 0", "footer")
        else:
            buttons.ibutton("👤 My Tasks", f"canall {owner_id} scope {owner_id}", "footer")
    buttons.ibutton("Close", f"canall {owner_id} close", "footer")
    whose = "<b>all tasks of the bot</b>" if not scope else "<b>your tasks</b>"
    return f"Choose which of {whose} to cancel.", buttons.build_menu(2)


async def cancell_all_buttons(_, message):
    user_id = message.from_user.id
    scope = 0 if _is_sudo(user_id) else user_id
    async with download_dict_lock:
        count = sum(
            1
            for dl in download_dict.values()
            if not scope or dl.message.from_user.id == scope
        )
    if count == 0:
        await sendMessage(message, "No active tasks!")
        return
    text, button = cancel_all_menu(user_id, scope)
    can_msg = await sendMessage(message, text, button)
    await auto_delete_message(message, can_msg)


@new_task
async def cancel_all_update(_, query):
    data = query.data.split()
    message = query.message
    reply_to = message.reply_to_message
    if len(data) < 3 or not data[1].isdigit():
        await query.answer()
        return await deleteMessage(message)
    owner_id = int(data[1])
    if query.from_user.id != owner_id:
        return await query.answer("This is not for you!", show_alert=True)
    if data[2] == "close":
        await query.answer()
        await deleteMessage(reply_to)
        await deleteMessage(message)
    elif data[2] == "scope":
        await query.answer()
        scope = int(data[3]) if _is_sudo(owner_id) else owner_id
        text, button = cancel_all_menu(owner_id, scope)
        await editMessage(message, text, button)
    else:
        scope = int(data[2])
        if not scope and not _is_sudo(owner_id):
            scope = owner_id
        status = " ".join(data[3:])
        await query.answer("Cancelling...")
        res = await cancel_all(status, scope or None)
        if not res:
            await sendMessage(reply_to or message, f"No matching tasks for {status}!")


async def retry_task(client, query):
    token = query.data.split()[1]
    data = retry_tasks.get(token)
    if data is None:
        await query.answer("Retry is not available anymore!", show_alert=True)
        return await editReplyMarkup(query.message, None)
    user_id, text, starter = data
    if query.from_user.id != user_id and not _is_sudo(query.from_user.id):
        return await query.answer("This is not for you!", show_alert=True)
    retry_tasks.pop(token, None)
    await query.answer("Retrying...")
    await editReplyMarkup(query.message, None)
    # the command is sent again (the first message may be deleted already)
    nextmsg = await sendMessage(query.message, text)
    if isinstance(nextmsg, str):
        return
    nextmsg = await client.get_messages(chat_id=nextmsg.chat.id, message_ids=nextmsg.id)
    nextmsg.from_user = query.from_user if query.from_user.id == user_id else await client.get_users(user_id)
    starter(client, nextmsg)


async def cancel_multi(_, query):
    tag = query.data.split()[1]
    owner = multi_tags.get(tag)
    if owner is None:
        await query.answer("This multi task already finished or stopped!", show_alert=True)
        return await editReplyMarkup(query.message, None)
    if query.from_user.id != owner and not _is_sudo(query.from_user.id):
        return await query.answer("This is not for you!", show_alert=True)
    multi_tags.pop(tag, None)
    await query.answer("Multi stopped! Running tasks keep going.", show_alert=True)
    await editReplyMarkup(query.message, None)


bot.add_handler(
    MessageHandler(
        cancel_mirror,
        filters=regex(f"^/{BotCommands.CancelMirror}(_\w+)?(?!all)")
        & CustomFilters.authorized
        & ~CustomFilters.blacklisted,
    )
)
bot.add_handler(
    MessageHandler(
        cancell_all_buttons,
        filters=command(BotCommands.CancelAllCommand)
        & CustomFilters.authorized
        & ~CustomFilters.blacklisted,
    )
)
bot.add_handler(CallbackQueryHandler(cancel_all_update, filters=regex(r"^canall")))
bot.add_handler(CallbackQueryHandler(cancel_multi, filters=regex(r"^cmulti")))
bot.add_handler(CallbackQueryHandler(retry_task, filters=regex(r"^retry")))
