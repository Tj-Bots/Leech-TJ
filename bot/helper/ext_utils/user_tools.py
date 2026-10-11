#!/usr/bin/env python3
from os import walk, path as ospath

from aiofiles.os import remove as aioremove, path as aiopath

from bot import LOGGER
from bot.helper.ext_utils.bot_utils import sync_to_async


def parse_extensions(value):
    exts = []
    for ext in str(value or "").replace(",", " ").split():
        ext = ext.strip().lstrip(".").lower()
        if ext and ext not in exts:
            exts.append(ext)
    return exts


async def remove_excluded(path, exts):
    """Delete files whose extension is in exts. Returns how many were removed."""
    if not exts:
        return 0
    suffixes = tuple(f".{ext}" for ext in exts)
    removed = 0
    if await aiopath.isfile(path):
        targets = [path] if path.lower().endswith(suffixes) else []
    else:
        targets = []
        for dirpath, _, files in await sync_to_async(walk, path):
            targets.extend(
                ospath.join(dirpath, f) for f in files if f.lower().endswith(suffixes)
            )
    for target in targets:
        try:
            await aioremove(target)
            removed += 1
        except Exception as e:
            LOGGER.error(f"Excluded Extensions: can't remove {target}: {e}")
    if removed:
        LOGGER.info(f"Excluded Extensions: removed {removed} file(s) from {path}")
    return removed


def parse_layout(value):
    value = str(value or "").strip().lower().replace("*", "x")
    parts = value.split("x")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        return None
    cols, rows = int(parts[0]), int(parts[1])
    if not (1 <= cols <= 10 and 1 <= rows <= 10) or cols * rows < 2:
        return None
    return f"{cols}x{rows}"


def parse_named_lines(value, sep=None):
    """'name value' (or 'name: value') per line -> dict."""
    result = {}
    for line in str(value or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if sep and sep in line:
            name, val = line.split(sep, 1)
        else:
            parts = line.split(maxsplit=1)
            if len(parts) < 2:
                continue
            name, val = parts
        name, val = name.strip(), val.strip()
        if name and val:
            result[name] = val
    return result


def parse_user_setting(key, value):
    """Validate a text user setting. Returns None when the value is invalid."""
    value = str(value or "").strip()
    if key == "excluded_ext":
        return " ".join(parse_extensions(value)) or None
    if key == "thumb_layout":
        return parse_layout(value)
    if key in ["rclone_path", "rclone_flags"]:
        return value or None
    if key == "upload_paths":
        return parse_named_lines(value) or None
    if key == "ffmpeg_cmds":
        cmds = {}
        for name, cmd in parse_named_lines(value, ":").items():
            cmd = cmd.removeprefix("ffmpeg").strip()
            if "-i" in cmd.split():
                cmds[name] = cmd
        return cmds or None
    if key == "mega_login":
        parts = value.split(maxsplit=1)
        if len(parts) != 2 or "@" not in parts[0]:
            return None
        return {"email": parts[0], "password": parts[1]}
    return value or None


def show_user_setting(key, value):
    from html import escape

    if not value:
        return "Not Exists"
    if key == "mega_login":
        return f"<code>{escape(value.get('email', ''))}</code> | <code>********</code>"
    if isinstance(value, dict):
        return "\n" + "\n".join(
            f"{i}. <b>{escape(str(k))}</b> : <code>{escape(str(v))}</code>"
            for i, (k, v) in enumerate(value.items(), start=1)
        )
    return f"<code>{escape(str(value))}</code>"


async def get_grid_thumb(video_file, duration, layout):
    """Thumbnail made of cols x rows frames of the video. None on failure."""
    from asyncio import create_subprocess_exec, wait_for
    from asyncio.subprocess import PIPE

    from bot.helper.ext_utils.leech_utils import take_ss

    if not (layout := parse_layout(layout)):
        return None
    cols, rows = (int(x) for x in layout.split("x"))
    total = cols * rows
    res = await take_ss(video_file, duration, total=total, gen_ss=True)
    if not res:
        return None
    des_dir = res[0]
    output = ospath.join(des_dir, "grid.jpg")
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-start_number",
        "1",
        "-i",
        ospath.join(des_dir, "wz_thumb_%d.jpg"),
        "-vf",
        f"scale={max(640 // cols, 64)}:-2,tile={layout}",
        "-frames:v",
        "1",
        "-q:v",
        "2",
        output,
    ]
    try:
        proc = await create_subprocess_exec(*cmd, stderr=PIPE)
        _, err = await wait_for(proc.communicate(), timeout=60)
        if proc.returncode != 0 or not await aiopath.exists(output):
            LOGGER.error(f"Thumbnail Layout failed for {video_file}: {err.decode()}")
            output = None
    except Exception as e:
        LOGGER.error(f"Thumbnail Layout failed for {video_file}: {e}")
        output = None
    for no in range(1, total + 1):
        frame = ospath.join(des_dir, f"wz_thumb_{no}.jpg")
        if await aiopath.exists(frame):
            await aioremove(frame)
    if output is None:
        from aiofiles.os import rmdir

        try:
            await rmdir(des_dir)
        except Exception:
            pass
    return output
