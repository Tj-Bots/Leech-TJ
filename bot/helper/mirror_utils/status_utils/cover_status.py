#!/usr/bin/env python3
from bot.helper.ext_utils.bot_utils import MirrorStatus
from bot.helper.mirror_utils.status_utils.metadata_status import MetadataStatus


class CoverStatus(MetadataStatus):
    def status(self):
        return MirrorStatus.STATUS_COVER

    async def cancel_download(self):
        listener = self._MetadataStatus__listener
        listener.suproc = "cancelled"
        await listener.onUploadError("Cover stopped by user!")
