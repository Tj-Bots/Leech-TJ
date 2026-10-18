#!/usr/bin/env python3
from bot import LOGGER
from bot.helper.ext_utils.bot_utils import MirrorStatus
from bot.helper.mirror_utils.status_utils.metadata_status import MetadataStatus


class FFmpegStatus(MetadataStatus):
    def __init__(self, *args, status=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.__status = status or MirrorStatus.STATUS_FFMPEG

    def status(self):
        return self.__status

    async def cancel_download(self):
        listener = self._MetadataStatus__listener
        LOGGER.info(f"Cancelling FFmpeg Cmds: {self.name()}")
        if listener.suproc is not None and listener.suproc != "cancelled":
            try:
                listener.suproc.kill()
            except Exception:
                pass
        listener.suproc = "cancelled"
        await listener.onUploadError("FFmpeg Cmds stopped by user!")
