#!/usr/bin/env python3
from bot import LOGGER
from bot.helper.mirror_utils.status_utils.step_progress import StepProgress
from bot.helper.ext_utils.bot_utils import (
    EngineStatus,
    get_readable_file_size,
    MirrorStatus,
)


class SplitStatus(StepProgress):
    def __init__(self, name, size, gid, listener):
        self.__name = name
        self.__gid = gid
        self.__size = size
        self.__listener = listener
        self.upload_details = listener.upload_details
        self.message = listener.message
        self._step_init(getattr(listener, "dir", ""), size)

    def gid(self):
        return self.__gid

    def name(self):
        return self.__name

    def size(self):
        return get_readable_file_size(self.__size)

    def status(self):
        return MirrorStatus.STATUS_SPLITTING

    def download(self):
        return self

    async def cancel_download(self):
        LOGGER.info(f"Cancelling Split: {self.__name}")
        if self.__listener.suproc is not None:
            self.__listener.suproc.kill()
        else:
            self.__listener.suproc = "cancelled"
        await self.__listener.onUploadError("splitting stopped by user!")

    def eng(self):
        return EngineStatus().STATUS_SPLIT_MERGE
