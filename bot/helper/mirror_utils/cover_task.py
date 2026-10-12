#!/usr/bin/env python3
# /cover: a normal leech-like task that only re-sends the video (by file_id)
# with a cover, no download and no upload.
from secrets import token_hex

from aiofiles.os import path as aiopath

from bot import LOGGER, bot, download_dict, download_dict_lock
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.tmdb_utils import get_auto_cover, get_auto_thumbnail
from bot.helper.listeners.tasks_listener import MirrorLeechListener
from bot.helper.mirror_utils.status_utils.cover_status import CoverStatus
from bot.helper.mirror_utils.upload_utils.pyrogramEngine import COVER_KWARG
from bot.helper.telegram_helper.message_utils import sendMessage, sendStatusMessage


async def _clean_auto(auto_thumb):
    from os import path as ospath

    from aiofiles.os import remove, rmdir

    if not auto_thumb:
        return
    for path in (get_auto_cover(auto_thumb), auto_thumb):
        if path and await aiopath.exists(path):
            await remove(path)
    try:
        await rmdir(ospath.dirname(auto_thumb))
    except Exception:
        pass


@new_task
async def cover_task(client, message):
    reply = message.reply_to_message
    video = reply.video if reply else None
    if not video:
        await sendMessage(message, "<i>Reply to a Video to set its Cover!</i>")
        return
    if not COVER_KWARG:
        await sendMessage(message, "<i>This Telegram library has no cover support!</i>")
        return

    user_id = message.from_user.id
    if username := message.from_user.username:
        tag = f"@{username}"
    else:
        tag = message.from_user.mention
    listener = MirrorLeechListener(
        message,
        isLeech=True,
        tag=tag,
        leech_utils={"screenshots": 0, "thumb": ""},
    )
    listener.isCover = True
    listener.upload_details["mode"] = listener.upload_details["mode"].replace(
        "#Leech", "#Cover", 1
    )
    name = video.file_name or f"video_{video.file_unique_id}.mp4"
    size = video.file_size or 0

    async with download_dict_lock:
        download_dict[listener.uid] = CoverStatus(name, size, token_hex(5), listener)
    await listener.onDownloadStart()
    await sendStatusMessage(message)

    auto_thumb = None
    try:
        custom = f"Thumbnails/{user_id}.jpg"
        if await aiopath.exists(custom):
            cover = custom
        else:
            auto_thumb = await get_auto_thumbnail(name, False)
            cover = get_auto_cover(auto_thumb)
            if not cover:
                raise Exception("No poster found on TMDB for this video")
        if listener.suproc == "cancelled":
            return

        # no dump chat for covers: straight to PM, or the same chat
        if listener.isPM or not listener.isSuperGroup:
            dest, reply_id = user_id, None
        else:
            dest, reply_id = message.chat.id, message.id
        kwargs = dict(
            chat_id=dest,
            video=video.file_id,
            caption=reply.caption or "",
            caption_entities=reply.caption_entities,
            duration=video.duration or 0,
            width=video.width or 0,
            height=video.height or 0,
            supports_streaming=True,
            disable_notification=True,
            reply_to_message_id=reply_id,
        )
        kwargs[COVER_KWARG] = cover
        try:
            sent = await bot.send_video(**kwargs)
        except Exception as e:
            if dest != user_id or not listener.isSuperGroup:
                raise
            # bot not started in PM, send it in the group instead
            LOGGER.error(f"Cover: can't send to PM of {user_id}: {e}")
            kwargs.update(chat_id=message.chat.id, reply_to_message_id=message.id)
            sent = await bot.send_video(**kwargs)

        files = {sent.link: name} if sent.chat.id != user_id else {}
        await listener.onUploadComplete(None, size, files, 1, 0, name)
    except Exception as e:
        LOGGER.error(f"Cover failed: {e}")
        await listener.onUploadError(str(e))
    finally:
        await _clean_auto(auto_thumb)
