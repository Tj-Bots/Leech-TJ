#!/usr/bin/env python3
# /cover: a normal leech-like task that only re-sends the video (by file_id)
# with a cover, no download and no upload.
from secrets import token_hex

from aiofiles.os import path as aiopath

from bot import LOGGER, bot, config_dict, download_dict, download_dict_lock, user_data
from bot.helper.ext_utils.task_manager import task_utils
from bot.helper.mirror_utils.hyper_utils import get_dump_chat
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import check_botpm
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.tmdb_utils import get_auto_cover, get_auto_thumbnail, user_lang
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

    # same checks as /leech (token, force sub, bot PM, limits)
    error_msg, error_button = await task_utils(message)
    user_dict = user_data.get(user_id, {})
    pm_checked = not await CustomFilters.sudo("", message) and (
        config_dict["BOT_PM"] or user_dict.get("bot_pm") or config_dict["SAFE_MODE"]
    )
    if message.chat.type != message.chat.type.BOT and not pm_checked:
        # covers always go to PM, so check it even when Bot PM is off
        _msg, error_button = await check_botpm(message, error_button)
        if _msg:
            error_msg.append(_msg)
    if error_msg:
        final_msg = f"<b><i>User:</i> {tag}</b>,\n"
        for index, _msg in enumerate(error_msg, 1):
            final_msg += f"\n<b>{index}</b>: {_msg}\n"
        if error_button is not None:
            error_button = error_button.build_menu(2)
        await sendMessage(message, final_msg, error_button)
        return
    listener = MirrorLeechListener(
        message,
        isLeech=True,
        tag=tag,
        leech_utils={"screenshots": 0, "thumb": ""},
    )
    listener.isCover = True
    # covers always go to PM, like a leech with Bot PM
    listener.isPM = True
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
            auto_thumb = await get_auto_thumbnail(
                name, False, user_lang(message.from_user)
            )
            cover = get_auto_cover(auto_thumb)
            if not cover:
                raise Exception("No poster found on TMDB for this video")
        if listener.suproc == "cancelled":
            return

        dump_chat = await get_dump_chat() if config_dict["COVER_DUMP"] else None
        kwargs = dict(
            chat_id=dump_chat or user_id,
            video=video.file_id,
            caption=reply.caption or "",
            caption_entities=reply.caption_entities,
            duration=video.duration or 0,
            width=video.width or 0,
            height=video.height or 0,
            supports_streaming=True,
            disable_notification=True,
        )
        kwargs[COVER_KWARG] = cover
        sent = await bot.send_video(**kwargs)
        if dump_chat:
            try:
                await bot.copy_message(user_id, sent.chat.id, sent.id)
            except Exception as e:
                LOGGER.error(f"Cover: can't send to PM of {user_id}: {e}")

        # same completion message as a leech, the name is a link only when
        # the cover was saved in the dump chat
        files = {(sent.link if dump_chat else ""): name}
        await listener.onUploadComplete(None, size, files, 1, 0, name)
    except Exception as e:
        LOGGER.error(f"Cover failed: {e}")
        await listener.onUploadError(str(e))
    finally:
        await _clean_auto(auto_thumb)
