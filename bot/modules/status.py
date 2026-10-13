#!/usr/bin/env python3
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex
from psutil import cpu_percent, virtual_memory, disk_usage
from time import time
from asyncio import sleep
from contextlib import suppress
from html import escape

from pyrogram.enums import ChatType

from bot import (
    bot_cache,
    status_reply_dict_lock,
    download_dict,
    download_dict_lock,
    botStartTime,
    Interval,
    config_dict,
    bot,
    OWNER_ID,
    user_data,
    LOGGER,
)
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    editMessage,
    deleteMessage,
    auto_delete_message,
    sendStatusMessage,
    user_info,
    update_all_messages,
    delete_all_messages,
    hold_status,
    release_status,
)
from bot.helper.ext_utils.bot_utils import (
    get_readable_file_size,
    get_readable_time,
    turn_page,
    setInterval,
    new_task,
    getDownloadByGid,
    RichText,
)
from bot.helper.themes import BotTheme
from bot.helper.telegram_helper.button_build import ButtonMaker

try:
    from pyrogram.enums import ButtonStyle

    DANGER, SUCCESS = ButtonStyle.DANGER, ButtonStyle.SUCCESS
except ImportError:
    DANGER = SUCCESS = None


@new_task
async def mirror_status(_, message):
    args = message.text.split()
    user_id = None
    if len(args) > 1:
        if args[1].lower() == "me":
            user_id = message.from_user.id
        elif args[1].isdigit():
            user_id = int(args[1])
    async with download_dict_lock:
        count = len(download_dict)
        if user_id:
            count = sum(
                1 for dl in download_dict.values() if dl.message.from_user.id == user_id
            )
    if count == 0 and user_id:
        reply_message = await sendMessage(
            message, f"<i>No active tasks for <code>{user_id}</code>!</i>"
        )
        await auto_delete_message(message, reply_message)
    elif count == 0:
        currentTime = get_readable_time(time() - botStartTime)
        free = get_readable_file_size(disk_usage(config_dict["DOWNLOAD_DIR"]).free)
        msg = BotTheme(
            "NO_ACTIVE_DL",
            cpu=cpu_percent(),
            free=free,
            free_p=round(100 - disk_usage(config_dict["DOWNLOAD_DIR"]).percent, 1),
            ram=virtual_memory().percent,
            uptime=currentTime,
        )
        reply_message = await sendMessage(message, msg)
        await auto_delete_message(message, reply_message)
    else:
        await sendStatusMessage(message, user_id)
        await deleteMessage(message)
        async with status_reply_dict_lock:
            if Interval:
                Interval[0].cancel()
                Interval.clear()
                Interval.append(
                    setInterval(
                        config_dict["STATUS_UPDATE_INTERVAL"], update_all_messages
                    )
                )


def _confirm_content(dl, gid, user):
    """Question in the text, Yes / No as inline keyboard buttons."""
    user_id = user.id
    name = f"<code>{escape(dl.name())}</code>"
    tag = f'<a href="tg://user?id={user_id}">{escape(user.first_name or str(user_id))}</a>'
    head = f"㊂ <b><u>Cancel Task :</u></b> {tag}"
    buttons = ButtonMaker()
    buttons.ibutton("Yes, Cancel", f"status cyes {gid}", style=DANGER)
    buttons.ibutton("No", f"status cno {user_id}", style=SUCCESS)
    if hasattr(bot, "send_rich_message"):
        text = RichText(
            f"<p>{head}</p><blockquote>╭ <b>Cancel this task?</b><br>\u200e╰ {name}</blockquote>"
        )
    else:
        text = f"{head}\n\n<blockquote>╭ <b>Cancel this task?</b>\n\u200e╰ {name}</blockquote>"
    return text, buttons.build_menu(2)


async def _send_confirm(query, dl, gid):
    message = query.message
    user_id = query.from_user.id
    text, buttons = _confirm_content(dl, gid, query.from_user)
    if message.chat.type != ChatType.PRIVATE:
        # group: the status is replaced only for the user who pressed
        try:
            from pyrogram.types import (
                EphemeralMessageParameters,
                InputRichMessage,
                ReplyParameters,
            )

            eph = EphemeralMessageParameters(
                receiver_user_id=user_id,
                callback_query_id=query.id,
                replace_callback_query_message=True,
            )
            if isinstance(text, RichText):
                await bot.send_rich_message(
                    message.chat.id,
                    InputRichMessage(html=str(text)),
                    reply_markup=buttons,
                    reply_parameters=ReplyParameters(message_id=message.id),
                    ephemeral_message_parameters=eph,
                )
            else:
                await bot.send_message(
                    message.chat.id,
                    text,
                    reply_markup=buttons,
                    reply_parameters=ReplyParameters(message_id=message.id),
                    ephemeral_message_parameters=eph,
                )
            with suppress(Exception):
                await query.answer()
            return
        except Exception as e:
            LOGGER.warning(f"Ephemeral confirm failed, editing the status: {e}")
    # private chat (only this user sees it): edit the status message itself
    await query.answer()
    hold_status(message.id)
    await editMessage(message, text, buttons)


async def _close_confirm(query):
    message = query.message
    if eph_id := getattr(message, "ephemeral_message_id", None):
        with suppress(Exception):
            await bot.delete_ephemeral_message(
                message.chat.id, query.from_user.id, eph_id
            )
            return
    # the status message itself was edited: bring the status back
    release_status(message.id)
    await update_all_messages(True)


def _can_manage(user_id, dl):
    return (
        OWNER_ID == user_id
        or dl.message.from_user.id == user_id
        or user_data.get(user_id, {}).get("is_sudo")
    )


@new_task
async def status_pages(_, query):
    data = query.data.split()
    user_id = query.from_user.id
    if data[1] == "cno":
        if len(data) > 2 and int(data[2]) != user_id:
            return await query.answer("This is not for you!", show_alert=True)
        await query.answer()
        return await _close_confirm(query)
    if data[1] in ["cancel", "cyes", "sel"] and len(data) > 2:
        dl = await getDownloadByGid(data[2])
        if dl is None:
            await query.answer("This task is already done!", show_alert=True)
            if data[1] == "cyes":
                await _close_confirm(query)
            return
        if not _can_manage(user_id, dl):
            return await query.answer("This task is not for you!", show_alert=True)
        if data[1] == "cancel":
            await _send_confirm(query, dl, data[2])
        elif data[1] == "cyes":
            await query.answer("Cancelling...")
            await dl.download().cancel_download()
            await _close_confirm(query)
        else:
            from bot.modules.torrent_select import start_selection

            await query.answer()
            await start_selection(query.message, dl)
        return
    if data[1] == "ref":
        await update_all_messages(True)
    elif data[1] in ["nex", "pre"]:
        await turn_page(data)
        await update_all_messages(True)
    elif data[1] == "close":
        await delete_all_messages()
    await query.answer()


bot.add_handler(
    MessageHandler(
        mirror_status,
        filters=command(BotCommands.StatusCommand)
        & CustomFilters.authorized
        & ~CustomFilters.blacklisted,
    )
)
bot.add_handler(CallbackQueryHandler(status_pages, filters=regex("^status")))
