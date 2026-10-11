#!/usr/bin/env python3
from os import walk, path as ospath

from aiofiles.os import remove as aioremove, path as aiopath

from bot import LOGGER, config_dict, user_data
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


def stop_dup_enabled(user_id):
    user_dict = user_data.get(user_id, {})
    if "stop_duplicate" in user_dict:
        return bool(user_dict["stop_duplicate"])
    return bool(config_dict["STOP_DUPLICATE"])


def any_stop_dup():
    return bool(config_dict["STOP_DUPLICATE"]) or any(
        ud.get("stop_duplicate") for ud in list(user_data.values())
    )


def user_rc_path(user_id):
    return user_data.get(user_id, {}).get("rclone_path") or config_dict["RCLONE_PATH"]


def user_rc_flags(user_id):
    return user_data.get(user_id, {}).get("rclone_flags") or config_dict["RCLONE_FLAGS"]


def resolve_upload_path(user_id, up):
    if not up or not isinstance(up, str):
        return up
    paths = user_data.get(user_id, {}).get("upload_paths") or {}
    for name, dest in paths.items():
        if name.casefold() == up.casefold():
            return dest
    return up


def user_cookie(user_id):
    path = f"cookies/{user_id}.txt"
    if user_data.get(user_id, {}).get("cookies") and ospath.exists(path):
        return path
    return "cookies.txt"


def resolve_ffmpeg_cmds(user_id, arg):
    """-ff value -> list of ffmpeg arg strings from the user's FFmpeg Cmds."""
    if not arg or not isinstance(arg, str):
        return []
    saved = user_data.get(user_id, {}).get("ffmpeg_cmds") or {}
    cmds = []
    for name in arg.replace(",", " ").split():
        for key, cmd in saved.items():
            if key.casefold() == name.casefold():
                cmds.append(cmd)
                break
    return cmds


async def _media_kind(path):
    from bot.helper.ext_utils.leech_utils import get_document_type

    try:
        is_video, is_audio, _ = await get_document_type(path)
    except Exception:
        return None
    if is_video:
        return "video"
    if is_audio:
        return "audio"
    return None


def _wanted(path, kind, want):
    if want == "all":
        return True
    if want in ("video", "audio"):
        return kind == want
    return path.lower().endswith(want)


async def run_ffmpeg_cmds(listener, path, cmds):
    """Run the user's ffmpeg commands on path (file or folder).
    Returns the path to upload, or None when cancelled."""
    from asyncio import create_subprocess_exec
    from asyncio.subprocess import PIPE
    from shlex import split as ssplit

    from aiofiles.os import makedirs, rename
    from aioshutil import move

    for raw in cmds:
        try:
            parts = ssplit(raw)
        except ValueError as e:
            LOGGER.error(f"FFmpeg Cmds: bad command {raw}: {e}")
            continue
        delete_src = "-del" in parts
        parts = [p for p in parts if p != "-del"]
        if "-i" not in parts or parts.index("-i") + 1 >= len(parts):
            LOGGER.error(f"FFmpeg Cmds: skipping command without -i: {raw}")
            continue
        in_idx = parts.index("-i") + 1
        in_token = parts[in_idx]
        if in_token.endswith(".video"):
            want = "video"
        elif in_token.endswith(".audio"):
            want = "audio"
        elif "." not in in_token:
            want = "all"
        else:
            want = ospath.splitext(in_token)[1].lower()

        single = await aiopath.isfile(path)
        if single:
            files = [path]
        else:
            files = []
            for dirpath, _, fnames in await sync_to_async(walk, path):
                files.extend(ospath.join(dirpath, f) for f in sorted(fnames))

        for f_path in files:
            if listener.suproc == "cancelled":
                return None
            kind = await _media_kind(f_path)
            if kind is None or not _wanted(f_path, kind, want):
                continue
            base, ext = ospath.splitext(f_path)
            fdir, fbase = ospath.split(base)
            cmd = list(parts)
            cmd[in_idx] = f_path
            outputs = []
            for idx, token in enumerate(cmd):
                if idx == in_idx or not token.startswith("mltb"):
                    continue
                tbase, text = ospath.splitext(token)
                if token == "mltb" or tbase == "mltb" and text == ext:
                    out = ospath.join(fdir, f"ffmpeg{idx}.{fbase}{text or ext}")
                else:
                    out = ospath.join(fdir, token.replace("mltb", fbase, 1))
                    if not text:
                        out += ext
                cmd[idx] = out
                outputs.append(out)
            if not outputs:
                LOGGER.error(f"FFmpeg Cmds: no mltb output in: {raw}")
                break
            existed = {out for out in outputs if await aiopath.exists(out)}
            LOGGER.info(f"FFmpeg Cmds: running on {f_path}")
            listener.suproc = await create_subprocess_exec(
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *cmd,
                stdout=PIPE, stderr=PIPE,
            )
            _, stderr = await listener.suproc.communicate()
            code = listener.suproc.returncode
            if listener.suproc == "cancelled" or code == -9:
                return None
            if code != 0:
                LOGGER.error(
                    f"FFmpeg Cmds failed for {f_path}: {stderr.decode(errors='ignore').strip()}"
                )
                for out in outputs:
                    if out not in existed and await aiopath.exists(out):
                        await aioremove(out)
                continue
            if delete_src:
                await aioremove(f_path)
                if len(outputs) == 1 and ospath.basename(outputs[0]).startswith(
                    "ffmpeg"
                ):
                    clean = ospath.join(
                        fdir, ospath.basename(outputs[0]).split(".", 1)[1]
                    )
                    await rename(outputs[0], clean)
                    outputs = [clean]
            if single:
                if delete_src and len(outputs) == 1:
                    path = outputs[0]
                else:
                    # keep the original and the new files together
                    folder = base if not await aiopath.exists(base) else f"{base}_ff"
                    await makedirs(folder, exist_ok=True)
                    for item in ([] if delete_src else [f_path]) + outputs:
                        await move(item, ospath.join(folder, ospath.basename(item)))
                    path = folder
                break
    return path
