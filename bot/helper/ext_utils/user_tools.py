#!/usr/bin/env python3
import re
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
    if key in ("sample_video", "screenshots"):
        top = 30 if key == "sample_video" else 10
        return int(value) if value.isdigit() and 1 <= int(value) <= top else None
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


UPLOAD_NAMES = {"gd": "GDrive", "rc": "RClone", "ddl": "DDL"}


def default_upload(user_id):
    """The user's own upload destination (gd / rc / ddl), else the bot's."""
    if (up := user_data.get(user_id, {}).get("default_upload")) in UPLOAD_NAMES:
        return up
    return config_dict["DEFAULT_UPLOAD"]


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


async def _run_ff(listener, cmd):
    from asyncio import create_subprocess_exec
    from asyncio.subprocess import PIPE

    listener.suproc = await create_subprocess_exec(
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *cmd,
        stdout=PIPE, stderr=PIPE,
    )
    _, stderr = await listener.suproc.communicate()
    code = listener.suproc.returncode
    if code != 0 and listener.suproc != "cancelled":
        LOGGER.error(f"FFmpeg error: {stderr.decode(errors='ignore').strip()}")
    return code == 0


async def make_sample_and_screenshots(listener, path, sample_secs, ss_count):
    """Create SAMPLE.<name> (stream copy, fast) and screenshots next to every
    video. A single file becomes a folder. Returns the new path, None if cancelled."""
    from aiofiles.os import makedirs
    from aioshutil import move

    from bot.helper.ext_utils.leech_utils import get_media_info

    single = await aiopath.isfile(path)
    if single:
        videos = [path] if await _media_kind(path) == "video" else []
    else:
        videos = []
        for dirpath, _, fnames in await sync_to_async(walk, path):
            for f in sorted(fnames):
                f_path = ospath.join(dirpath, f)
                if not f.startswith("SAMPLE.") and await _media_kind(f_path) == "video":
                    videos.append(f_path)
    if not videos:
        return path
    if single:
        base = ospath.splitext(path)[0]
        folder = base if not await aiopath.exists(base) else f"{base}_extras"
        await makedirs(folder, exist_ok=True)
        new_file = ospath.join(folder, ospath.basename(path))
        await move(path, new_file)
        videos, path = [new_file], folder

    for video in videos:
        if listener.suproc == "cancelled":
            return None
        duration = (await get_media_info(video))[0] or 0
        if duration <= 0:
            continue
        vdir, vname = ospath.split(video)
        vbase = ospath.splitext(vname)[0]
        if sample_secs:
            secs = min(sample_secs, duration)
            start = max(0, duration / 2 - secs / 2)
            await _run_ff(
                listener,
                [
                    "-ss", f"{start:.2f}", "-i", video, "-t", f"{secs:.2f}",
                    "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy",
                    "-avoid_negative_ts", "make_zero",
                    ospath.join(vdir, f"SAMPLE.{vname}"),
                ],
            )
        for no in range(1, (ss_count or 0) + 1):
            if listener.suproc == "cancelled":
                return None
            stamp = duration * no / (ss_count + 1)
            await _run_ff(
                listener,
                [
                    "-ss", f"{stamp:.2f}", "-i", video, "-frames:v", "1",
                    "-q:v", "2", ospath.join(vdir, f"{vbase}.SS{no:02}.jpg"),
                ],
            )
    return path


def media_store_enabled(user_id):
    user_dict = user_data.get(user_id, {})
    if "media_store" in user_dict:
        return bool(user_dict["media_store"])
    return bool(config_dict.get("MEDIA_STORE"))


def encode_store(chat_id, msg_id):
    from base64 import urlsafe_b64encode

    raw = f"file{chat_id}&&{msg_id}".encode()
    return urlsafe_b64encode(raw).decode().rstrip("=")


def decode_store(param):
    """start param -> (chat_id, msg_id) or None"""
    from base64 import urlsafe_b64decode

    try:
        raw = urlsafe_b64decode(param + "=" * (-len(param) % 4)).decode()
    except Exception:
        return None
    if not raw.startswith("file") or "&&" not in raw:
        return None
    chat, msg = raw[4:].split("&&", 1)
    if not msg.isdigit():
        return None
    return (int(chat) if chat.lstrip("-").isdigit() else chat), int(msg)


def store_link(bot_name, file_link):
    """Telegram message link -> t.me/bot?start=... or None"""
    parts = str(file_link).rstrip("/").split("/")
    if len(parts) < 2 or not parts[-1].isdigit():
        return None
    msg_id = int(parts[-1])
    if "c" in parts[:-1]:
        # /c/<chat>/<msg> or topic links /c/<chat>/<topic>/<msg>
        cid = parts[parts.index("c") + 1]
        chat = f"-100{cid}" if cid.isdigit() else None
    else:
        chat = parts[-2] if len(parts) >= 2 and parts[-2] != "t.me" else None
    if not chat:
        return None
    return f"https://t.me/{bot_name}?start={encode_store(chat, msg_id)}"


def parse_size(value):
    """-sp: '1.5GB', '2000MB', '2G' or bytes -> bytes (0 when invalid)."""
    m = re.match(r"^\s*([\d.]+)\s*([kmgt]?)i?b?\s*$", str(value or ""), re.I)
    if not m:
        return 0
    mult = {"": 1, "k": 1024, "m": 1024**2, "g": 1024**3, "t": 1024**4}[m[2].lower()]
    try:
        return int(float(m[1]) * mult)
    except ValueError:
        return 0


def parse_convert(value):
    """'mp3 + flac ogg' -> ('mp3', '+', ['.flac', '.ogg']), same rules as WZML-X."""
    data = str(value or "").split()
    if not data:
        return "", "", []
    ext = data[0].lower().lstrip(".")
    if len(data) > 2 and data[1] in ("+", "-"):
        return ext, data[1], [f".{e.lower().lstrip('.')}" for e in data[2:]]
    return ext, "", []


def _want_convert(f_path, target, mode, exts):
    low = f_path.lower()
    if not target or low.endswith(f".{target}"):
        return False
    if mode == "+":
        return low.endswith(tuple(exts))
    if mode == "-":
        return not low.endswith(tuple(exts))
    return True


AUDIO_CODECS = {
    "mp3": ["-c:a", "libmp3lame", "-q:a", "2"],
    "m4a": ["-c:a", "aac", "-b:a", "192k"],
    "aac": ["-c:a", "aac", "-b:a", "192k"],
    "opus": ["-c:a", "libopus", "-b:a", "128k"],
    "ogg": ["-c:a", "libvorbis", "-q:a", "5"],
    "flac": ["-c:a", "flac"],
    "wav": ["-c:a", "pcm_s16le"],
}


async def _extract_audio(listener, f_path, ext):
    output = f"{ospath.splitext(f_path)[0]}.{ext}"
    base_cmd = ["-i", f_path, "-map", "0:a:0", "-vn", "-sn", "-dn", "-map_metadata", "0"]
    LOGGER.info(f"Extracting audio: {f_path} -> {ext}")
    # fast: keep the audio as is when the container allows it
    done = False
    if ext not in ("mp3", "flac", "wav"):
        done = await _run_ff(listener, [*base_cmd, "-c:a", "copy", output])
    if not done and listener.suproc != "cancelled":
        done = await _run_ff(listener, [*base_cmd, *AUDIO_CODECS.get(ext, []), output])
    return done, output


async def convert_media(listener, path, audio_arg, video_arg, ea_arg=""):
    """-ca / -cv / -ea: convert audios and videos, or extract the audio of videos.
    Returns the new path, None if cancelled."""
    ea_ext = ""
    if ea_arg:
        ea_ext = "mp3" if ea_arg is True else str(ea_arg).split()[0].lower().lstrip(".")
    vext, vmode, vexts = parse_convert(video_arg)
    aext, amode, aexts = parse_convert(audio_arg)
    single = await aiopath.isfile(path)
    if single:
        files = [path]
    else:
        files = []
        for dirpath, _, fnames in await sync_to_async(walk, path):
            files.extend(ospath.join(dirpath, f) for f in fnames)

    for f_path in files:
        if listener.suproc == "cancelled":
            return None
        kind = await _media_kind(f_path)
        base = ospath.splitext(f_path)[0]
        if kind == "video" and ea_ext:
            done, output = await _extract_audio(listener, f_path, ea_ext)
        elif kind == "video" and _want_convert(f_path, vext, vmode, vexts):
            output = f"{base}.{vext}"
            LOGGER.info(f"Converting video: {f_path} -> {vext}")
            # fast: only change the container, keep all streams
            done = await _run_ff(listener, ["-i", f_path, "-map", "0", "-c", "copy", output])
            if not done and listener.suproc != "cancelled":
                sub_codec = {"mp4": "mov_text", "mkv": "ass"}.get(vext, "copy")
                done = await _run_ff(
                    listener,
                    ["-i", f_path, "-map", "0", "-c:v", "libx264", "-c:a", "aac",
                     "-c:s", sub_codec, output],
                )
        elif kind == "audio" and _want_convert(f_path, aext, amode, aexts):
            output = f"{base}.{aext}"
            LOGGER.info(f"Converting audio: {f_path} -> {aext}")
            done = await _run_ff(listener, ["-i", f_path, output])
            if not done and listener.suproc != "cancelled":
                # some formats can't keep the cover art, drop it
                done = await _run_ff(listener, ["-i", f_path, "-vn", output])
        else:
            continue
        if listener.suproc == "cancelled":
            return None
        if done:
            await aioremove(f_path)
            if single:
                return output
        elif await aiopath.exists(output):
            await aioremove(output)
    return path
