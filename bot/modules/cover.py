#!/usr/bin/env python3
from html import escape
from os import path as ospath
from time import time

from aiofiles.os import path as aiopath, remove as aioremove, rmdir
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler

from bot import LOGGER, bot, config_dict, user_data
from bot.helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from bot.helper.ext_utils.tmdb_utils import get_auto_cover, get_auto_thumbnail
from bot.helper.mirror_utils.hyper_utils import get_dump_chat
from bot.helper.mirror_utils.upload_utils.pyrogramEngine import COVER_KWARG
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import (
    deleteMessage,
    editMessage,
    sendMessage,
)
from bot.helper.themes import BotTheme

COVER_HELP = """㊂ <b><u>Cover Usage :</u></b>

<blockquote>╭ Reply to a <b>Video</b> with <code>/{cmd}</code>
┊ Uses your <b>Custom Thumbnail</b> as cover
╰ Or the <b>Auto Thumbnail</b> poster (TMDB) if no custom thumbnail</blockquote>

➲ <i>Set them in /{uset}</i>"""


async def _cleanup(thumb):
    if not thumb or ospath.basename(thumb) != "auto_thumb.jpg":
        return
    for path in (get_auto_cover(thumb), thumb):
        if path and await aiopath.exists(path):
            await aioremove(path)
    try:
        await rmdir(ospath.dirname(thumb))
    except Exception:
        pass


async def set_cover(_, message):
    start = time()
    reply = message.reply_to_message
    video = reply.video if reply else None
    if not video:
        return await sendMessage(
            message,
            COVER_HELP.format(
                cmd=BotCommands.CoverCommand, uset=BotCommands.UserSetCommand[0]
            ),
        )
    if not COVER_KWARG:
        return await sendMessage(message, "<i>This Telegram library has no cover support!</i>")

    from_user = message.from_user
    user_id = from_user.id
    user_dict = user_data.get(user_id, {})
    tag = from_user.mention(style="html")
    name = video.file_name or (reply.caption or "").split("\n")[0] or "video.mp4"

    auto_thumb = None
    custom = f"Thumbnails/{user_id}.jpg"
    if await aiopath.exists(custom):
        cover = custom
    elif user_dict.get("auto_thumb") and config_dict.get("TMDB_ACCESS_TOKEN"):
        status = await sendMessage(message, "<i>Searching poster on TMDB...</i>")
        auto_thumb = await get_auto_thumbnail(name, False)
        cover = get_auto_cover(auto_thumb) or auto_thumb
        await deleteMessage(status)
        if not cover:
            return await sendMessage(
                message,
                f"<i>No poster found on TMDB for</i> <code>{escape(name)}</code>",
            )
    else:
        return await sendMessage(
            message,
            "<i>Set a Custom Thumbnail or enable Auto Thumbnail in User Settings first!</i>",
        )

    status = await sendMessage(message, "<i>Setting Cover...</i>")
    try:
        target = await get_dump_chat() or user_id
        video_kwargs = dict(
            video=video.file_id,
            caption=reply.caption or "",
            caption_entities=reply.caption_entities,
            duration=video.duration or 0,
            width=video.width or 0,
            height=video.height or 0,
            supports_streaming=True,
            disable_notification=True,
        )
        video_kwargs[COVER_KWARG] = cover
        try:
            sent = await bot.send_video(chat_id=target, **video_kwargs)
        except Exception as e:
            if target == user_id:
                raise
            LOGGER.error(f"Cover: can't send to dump chat {target}: {e}")
            target = user_id
            sent = await bot.send_video(chat_id=target, **video_kwargs)

        in_pm = target == user_id
        if not in_pm:
            try:
                await bot.copy_message(user_id, sent.chat.id, sent.id)
                in_pm = True
            except Exception as e:
                LOGGER.error(f"Cover: can't send to PM of {user_id}: {e}")
    except Exception as e:
        LOGGER.error(f"Cover failed: {e}")
        await editMessage(
            status,
            f"<i>Cover failed! Start the bot in PM and try again.</i>\n<code>{escape(str(e))}</code>",
        )
        await _cleanup(auto_thumb)
        return
    await _cleanup(auto_thumb)
    await deleteMessage(status)

    msg = BotTheme("NAME", Name=escape(name))
    msg += BotTheme("SIZE", Size=get_readable_file_size(video.file_size or 0))
    msg += BotTheme("ELAPSE", Time=get_readable_time(time() - start))
    msg += BotTheme("MODE", Mode=" #Cover | #Tg")
    msg += BotTheme("L_TOTAL_FILES", Files=1)
    msg += BotTheme("L_CC", Tag=tag)
    msg += BotTheme("L_BOT_MSG") if in_pm else BotTheme("PM_BOT_MSG")
    if sent.chat.id != user_id and sent.link:
        msg += f"\n<blockquote>1. <a href='{sent.link}'>{escape(name)}</a></blockquote>"
    await sendMessage(message, msg)


bot.add_handler(
    MessageHandler(
        set_cover,
        filters=command(BotCommands.CoverCommand)
        & CustomFilters.authorized
        & ~CustomFilters.blacklisted,
    )
)
