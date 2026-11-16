#!/usr/bin/env python3
"""Progress of a processing step (split, FFmpeg, video tools...) like the Go bot:
Processed is what the step wrote in the task folder since it began, compared with the input
size; Speed is that divided by the time; ETA is what is left divided by the speed."""
from os import path as ospath, walk
from time import time

from bot.helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time


def _snapshot(folder):
    files = {}
    for dirpath, _, names in walk(folder):
        for n in names:
            p = ospath.join(dirpath, n)
            try:
                st = ospath.getsize(p), ospath.getmtime(p)
            except OSError:
                continue
            files[p] = st
    return files


class StepProgress:
    def _step_init(self, folder, size):
        self._st_folder = folder
        self._st_size = size or 0
        self._st_start = time()
        self._st_before = _snapshot(folder) if folder and ospath.isdir(folder) else {}
        self._st_cache = (0.0, 0)

    def processed_raw(self):
        at, val = self._st_cache
        if time() - at < 1:  # the status asks several times per refresh
            return val
        done = 0
        for p, st in _snapshot(self._st_folder).items():
            if self._st_before.get(p) != st:
                done += st[0]
        if self._st_size:
            done = min(done, self._st_size)
        self._st_cache = (time(), done)
        return done

    def speed_raw(self):
        return self.processed_raw() / max(time() - self._st_start, 1)

    def progress_raw(self):
        return self.processed_raw() / self._st_size * 100 if self._st_size else 0

    def progress(self):
        return f"{round(self.progress_raw(), 2)}%"

    def speed(self):
        return f"{get_readable_file_size(self.speed_raw())}/s"

    def eta(self):
        spd = self.speed_raw()
        if not spd or not self._st_size:
            return "-"
        return get_readable_time((self._st_size - self.processed_raw()) / spd)

    def processed_bytes(self):
        return get_readable_file_size(self.processed_raw())
