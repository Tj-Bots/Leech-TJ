#!/usr/bin/env python3
"""Video Tools (-vt): everything here is stream copy, nothing is re-encoded.
Owners can add their own ffmpeg commands with VT_CUSTOM_CMDS."""
from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from json import loads
from os import path as ospath, walk

from aiofiles.os import path as aiopath, remove as aioremove, rename as aiorename

from bot import LOGGER, config_dict
from bot.helper.ext_utils.bot_utils import sync_to_async
from bot.helper.ext_utils.user_tools import (
    _media_kind,
    _run_ff,
    convert_media,
    make_sample_and_screenshots,
    parse_named_lines,
    run_ffmpeg_cmds,
)

SUB_EXTS = (".srt", ".ass", ".ssa", ".vtt", ".sub")
AUDIO_EXT = {
    "aac": "m4a",
    "mp3": "mp3",
    "ac3": "ac3",
    "eac3": "eac3",
    "opus": "opus",
    "flac": "flac",
    "dts": "dts",
    "vorbis": "ogg",
    "truehd": "thd",
}
SUB_EXT = {"subrip": "srt", "ass": "ass", "ssa": "ass", "webvtt": "vtt"}


def custom_tools():
    """Owner's tools from VT_CUSTOM_CMDS: 'name: ffmpeg args' per line."""
    tools = {}
    for name, cmd in parse_named_lines(config_dict.get("VT_CUSTOM_CMDS", ""), ":").items():
        cmd = cmd.removeprefix("ffmpeg").strip()
        if "-i" in cmd.split():
            tools[name] = cmd
    return tools


async def _files(path):
    if await aiopath.isfile(path):
        return [path]
    files = []
    for dirpath, _, fnames in await sync_to_async(walk, path):
        files.extend(ospath.join(dirpath, f) for f in sorted(fnames))
    return files


async def _videos(path):
    return [f for f in await _files(path) if await _media_kind(f) == "video"]


async def _probe(f_path):
    proc = await create_subprocess_exec(
        "ffprobe", "-v", "error", "-print_format", "json", "-show_streams", f_path,
        stdout=PIPE, stderr=PIPE,
    )
    out, _ = await proc.communicate()
    try:
        return loads(out.decode()).get("streams", [])
    except Exception:
        return []


async def _replace(listener, src, out, cmd):
    """Run ffmpeg into out, then out replaces src. False on failure."""
    if not await _run_ff(listener, cmd):
        if await aiopath.exists(out):
            await aioremove(out)
        return False
    await aioremove(src)
    final = ospath.splitext(src)[0] + ospath.splitext(out)[1]
    await aiorename(out, final)
    return final


async def merge_videos(listener, path):
    videos = await _videos(path)
    if len(videos) < 2:
        return path
    base, ext = ospath.splitext(videos[0])
    lst = f"{base}.vt_list.txt"
    with open(lst, "w") as f:
        for v in videos:
            f.write("file '" + v.replace("'", "'\\''") + "'\n")
    out = f"{base}.merged{ext}"
    ok = await _run_ff(
        listener, ["-f", "concat", "-safe", "0", "-i", lst, "-map", "0", "-c", "copy", out]
    )
    await aioremove(lst)
    if ok:
        for v in videos:
            await aioremove(v)
    elif await aiopath.exists(out):
        await aioremove(out)
    return path


async def _mux_extra(listener, path, kind):
    """Video + Audio / Video + Subtitle: add the loose files into the video."""
    files = await _files(path)
    videos = [f for f in files if await _media_kind(f) == "video"]
    if not videos:
        return path
    if kind == "audio":
        extras = [f for f in files if f not in videos and await _media_kind(f) == "audio"]
    else:
        extras = [f for f in files if f.lower().endswith(SUB_EXTS)]
    if not extras:
        return path
    video = videos[0]
    base, ext = ospath.splitext(video)
    cmd = ["-i", video]
    for e in extras:
        cmd += ["-i", e]
    cmd += ["-map", "0"]
    for i in range(1, len(extras) + 1):
        cmd += ["-map", f"{i}:{'a' if kind == 'audio' else 's'}"]
    cmd += ["-c", "copy"]
    if kind == "subs" and ext.lower() == ".mp4":
        cmd += ["-c:s", "mov_text"]
    done = await _replace(listener, video, f"{base}.vt{ext}", cmd + [f"{base}.vt{ext}"])
    if not done and ext.lower() != ".mkv" and listener.suproc != "cancelled":
        # mp4 can't hold every codec, mkv can
        cmd = [c for c in cmd if c not in ("-c:s", "mov_text")]
        done = await _replace(listener, video, f"{base}.vt.mkv", cmd + [f"{base}.vt.mkv"])
    if done:
        for e in extras:
            await aioremove(e)
    return path


async def extract_streams(listener, path, kinds):
    for video in await _videos(path):
        base, ext = ospath.splitext(video)
        streams = await _probe(video)
        done = False
        for st in streams:
            ctype, codec, idx = st.get("codec_type"), st.get("codec_name", ""), st["index"]
            lang = (st.get("tags") or {}).get("language", "")
            tag = f".{lang}" if lang else ""
            if ctype == "audio" and "audio" in kinds:
                out = f"{base}.{idx}{tag}.{AUDIO_EXT.get(codec, 'mka')}"
                done |= await _run_ff(listener, ["-i", video, "-map", f"0:{idx}", "-c", "copy", out])
            elif ctype == "subtitle" and "subs" in kinds:
                sext = SUB_EXT.get(codec, "srt" if codec == "mov_text" else "mks")
                copy = "srt" if codec == "mov_text" else "copy"
                out = f"{base}.{idx}{tag}.{sext}"
                done |= await _run_ff(listener, ["-i", video, "-map", f"0:{idx}", "-c", copy, out])
        if "video" in kinds:
            out = f"{base}.video{ext}"
            done |= await _run_ff(listener, ["-i", video, "-map", "0:v", "-c", "copy", out])
        if done:
            await aioremove(video)
    return path


async def remove_streams(listener, path, kinds):
    for video in await _videos(path):
        base, ext = ospath.splitext(video)
        cmd = ["-i", video, "-map", "0"]
        if "subs" in kinds:
            cmd += ["-map", "-0:s"]
        if "audio" in kinds:
            cmd += ["-map", "-0:a", "-map", "0:a:0?"]
        if "attach" in kinds:
            cmd += ["-map", "-0:t"]
        out = f"{base}.vt{ext}"
        await _replace(listener, video, out, cmd + ["-c", "copy", out])
    return path


async def trim_videos(listener, path, start, end):
    for video in await _videos(path):
        base, ext = ospath.splitext(video)
        out = f"{base}.vt{ext}"
        cmd = ["-ss", start] + (["-to", end] if end else []) + ["-i", video]
        await _replace(
            listener, video, out, cmd + ["-map", "0", "-c", "copy", "-avoid_negative_ts", "make_zero", out]
        )
    return path


async def rename_output(path, new_name):
    if await aiopath.isfile(path):
        ext = ospath.splitext(path)[1]
        if not ospath.splitext(new_name)[1]:
            new_name += ext
    new_path = ospath.join(ospath.dirname(path.rstrip("/")), new_name)
    await aiorename(path, new_path)
    return new_path


async def run_video_tools(listener, path, sel):
    """Order: merge, remove, trim, extract, convert, owner tools, screenshots, rename.
    Returns the new path, or None when cancelled."""
    steps = [
        ("merge_video", lambda p: merge_videos(listener, p)),
        ("merge_audio", lambda p: _mux_extra(listener, p, "audio")),
        ("merge_subs", lambda p: _mux_extra(listener, p, "subs")),
        ("remove", lambda p: remove_streams(listener, p, sel["remove"])),
        ("trim", lambda p: trim_videos(listener, p, *sel["trim"])),
        ("extract", lambda p: extract_streams(listener, p, sel["extract"])),
    ]
    for key, func in steps:
        if not sel.get(key):
            continue
        LOGGER.info(f"Video Tools {key}: {path}")
        path = await func(path)
        if listener.suproc == "cancelled":
            return None
    if conv := sel.get("convert"):
        audio = conv in ("mp3", "m4a")
        path = await convert_media(listener, path, "", "" if audio else conv, conv if audio else "")
        if path is None or listener.suproc == "cancelled":
            return None
    if names := sel.get("custom"):
        tools = custom_tools()
        cmds = [tools[n] for n in names if n in tools]
        if cmds:
            path = await run_ffmpeg_cmds(listener, path, cmds)
            if path is None or listener.suproc == "cancelled":
                return None
    if count := sel.get("ss"):
        path = await make_sample_and_screenshots(listener, path, 0, count)
        if path is None or listener.suproc == "cancelled":
            return None
    if new_name := sel.get("rename"):
        try:
            path = await rename_output(path, new_name)
        except Exception as e:
            LOGGER.error(f"Video Tools rename failed: {e}")
    return path
