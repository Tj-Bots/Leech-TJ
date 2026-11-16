#!/usr/bin/env python3
"""Video Tools (-vt): everything here is stream copy, nothing is re-encoded.
Owners can add their own ffmpeg commands with VT_CUSTOM_CMDS."""
from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from json import loads
from os import path as ospath, walk
from re import split as re_split, sub as re_sub

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
            if ctype == "audio" and ("audio" in kinds or "all" in kinds):
                out = f"{base}.{idx}{tag}.{AUDIO_EXT.get(codec, 'mka')}"
                done |= await _run_ff(listener, ["-i", video, "-map", f"0:{idx}", "-c", "copy", out])
            elif ctype == "subtitle" and ("subs" in kinds or "all" in kinds):
                sext = SUB_EXT.get(codec, "srt" if codec == "mov_text" else "mks")
                copy = "srt" if codec == "mov_text" else "copy"
                out = f"{base}.{idx}{tag}.{sext}"
                done |= await _run_ff(listener, ["-i", video, "-map", f"0:{idx}", "-c", copy, out])
        if "video" in kinds or "all" in kinds:
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
    """New name for the video, the extension stays when none is given.
    A folder with one video: the video gets the name (and the folder too)."""
    if await aiopath.isfile(path):
        ext = ospath.splitext(path)[1]
        if not ospath.splitext(new_name)[1]:
            new_name += ext
        new_path = ospath.join(ospath.dirname(path), new_name)
        await aiorename(path, new_path)
        return new_path
    videos = await _videos(path)
    if len(videos) == 1:
        video = videos[0]
        ext = ospath.splitext(video)[1]
        vname = new_name if ospath.splitext(new_name)[1] else new_name + ext
        await aiorename(video, ospath.join(ospath.dirname(video), vname))
    new_path = ospath.join(ospath.dirname(path.rstrip("/")), ospath.splitext(new_name)[0])
    await aiorename(path, new_path)
    return new_path


async def strip_metadata(listener, path):
    """Global tags and stream titles go, the languages stay."""
    for video in await _videos(path):
        base, ext = ospath.splitext(video)
        out = f"{base}.vt{ext}"
        await _replace(listener, video, out, ["-i", video, "-map", "0", "-map_metadata:g", "-1",
            "-metadata:s", "title=", "-metadata:s", "handler_name=", "-c", "copy", out])
    return path


async def shift_streams(listener, path, kind, secs):
    """Audio Sync ("a") / Subtitle Sync ("s"): move those streams by secs seconds."""
    for video in await _videos(path):
        base, ext = ospath.splitext(video)
        out = f"{base}.vt{ext}"
        cmd = ["-i", video, "-itsoffset", str(secs), "-i", video, "-map", "0:v?"]
        cmd += ["-map", "1:a", "-map", "0:s?"] if kind == "a" else ["-map", "0:a?", "-map", "1:s"]
        cmd += ["-map", "0:t?", "-map_metadata", "0", "-map_chapters", "0", "-c", "copy", out]
        await _replace(listener, video, out, cmd)
    return path


async def _duration(f_path):
    proc = await create_subprocess_exec(
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
        "default=nw=1:nk=1", f_path, stdout=PIPE, stderr=PIPE,
    )
    out, _ = await proc.communicate()
    try:
        return float(out.decode().strip())
    except Exception:
        return 0


async def set_chapters(listener, path, mode):
    """Remove the chapters, or add one every N minutes."""
    for video in await _videos(path):
        base, ext = ospath.splitext(video)
        out = f"{base}.vt{ext}"
        if mode == "remove":
            await _replace(listener, video, out, ["-i", video, "-map", "0", "-map_chapters", "-1", "-c", "copy", out])
            continue
        total = int(await _duration(video) * 1000)
        step = int(mode) * 60000
        if total <= 0 or step <= 0:
            continue
        lines, no, start = [";FFMETADATA1"], 1, 0
        while start < total:
            end = min(start + step, total)
            lines += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={start}", f"END={end}", f"title=Chapter {no}"]
            no, start = no + 1, end
        meta = f"{base}.vt_chapters.txt"
        with open(meta, "w") as f:
            f.write("\n".join(lines) + "\n")
        await _replace(listener, video, out, ["-i", video, "-i", meta, "-map", "0", "-map_metadata", "0",
            "-map_chapters", "1", "-c", "copy", out])
        if await aiopath.exists(meta):
            await aioremove(meta)
    return path


async def default_audio(listener, path, want):
    """One audio track (number or language) becomes the first and default one."""
    want = str(want).lower()
    for video in await _videos(path):
        audio = [st for st in await _probe(video) if st.get("codec_type") == "audio"]
        pick = -1
        if want.isdigit():
            if 1 <= int(want) <= len(audio):
                pick = int(want) - 1
        else:
            for i, st in enumerate(audio):
                lang = ((st.get("tags") or {}).get("language") or "").lower()
                if lang and (lang == want or lang.startswith(want) or want.startswith(lang)):
                    pick = i
                    break
        if pick < 0:
            continue
        base, ext = ospath.splitext(video)
        out = f"{base}.vt{ext}"
        cmd = ["-i", video, "-map", "0:v?", "-map", f"0:a:{pick}"]
        cmd += sum((["-map", f"0:a:{i}"] for i in range(len(audio)) if i != pick), [])
        cmd += ["-map", "0:s?", "-map", "0:t?", "-map_metadata", "0", "-map_chapters", "0", "-c", "copy",
                "-disposition:a:0", "default"]
        cmd += sum(([f"-disposition:a:{i}", "0"] for i in range(1, len(audio))), [])
        await _replace(listener, video, out, cmd + [out])
    return path


async def split_audio(listener, path, minutes):
    """Cut audio files into parts of the given minutes."""
    secs = int(minutes) * 60
    for f in await _files(path):
        if await _media_kind(f) != "audio" or await _duration(f) <= secs:
            continue
        base, ext = ospath.splitext(f)
        if await _run_ff(listener, ["-i", f, "-map", "0:a", "-c", "copy", "-f", "segment",
                "-segment_time", str(secs), "-reset_timestamps", "1", f"{base}.part%03d{ext}"]):
            await aioremove(f)
    return path


# ---- Translate Subtitles (Google Translate, several addresses: one may ask for a captcha) ----

async def _google_translate(session, text, lang):
    for host in ("translate.googleapis.com", "translate.google.com"):
        url = f"https://{host}/translate_a/single?client=gtx&sl=auto&dt=t&tl={lang}"
        try:
            async with session.post(url, data={"q": text}, timeout=40) as resp:
                if resp.status != 200:
                    continue
                data = loads(await resp.text())
                return "".join(seg[0] for seg in data[0] if seg and seg[0])
        except Exception:
            continue
    try:
        url = f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl={lang}"
        async with session.post(url, data={"q": text}, timeout=40) as resp:
            data = loads(await resp.text())
            first = data[0]
            return first if isinstance(first, str) else first[0]
    except Exception:
        return None


async def _translate_srt(src, dst, lang):
    from aiohttp import ClientSession

    with open(src, encoding="utf-8", errors="ignore") as f:
        body = f.read().lstrip("\ufeff").replace("\r\n", "\n").strip()
    cues = []
    for block in re_split(r"\n{2,}", body):
        lines = block.split("\n")
        i = next((n for n, line in enumerate(lines) if "-->" in line), None)
        if i is not None:
            cues.append(("\n".join(lines[: i + 1]), "\n".join(lines[i + 1 :])))
    if not cues:
        return False
    sep = " ⏎ "
    out = [c[1] for c in cues]
    async with ClientSession() as session:
        start = 0
        while start < len(cues):
            end, size = start, 0
            while end < len(cues) and size < 3500:
                size += len(cues[end][1]) + 1
                end += 1
            lines = [c[1].strip().replace("\n", sep) for c in cues[start:end]]
            res = await _google_translate(session, "\n".join(lines), lang)
            got = res.rstrip("\n").split("\n") if res else []
            if len(got) == end - start:
                out[start:end] = got
            else:  # the line count changed: one cue at a time
                for i in range(start, end):
                    t = await _google_translate(session, lines[i - start], lang)
                    out[i] = (t or lines[i - start]).replace("\n", " ")
            start = end
    with open(dst, "w", encoding="utf-8") as f:
        for (head, _), text in zip(cues, out):
            text = re_sub(r"\s*⏎\s*", "\n", text.strip())
            f.write(f"{head}\n{text}\n\n")
    return True


async def translate_subs(listener, path, lang):
    """.srt files get a translated copy next to them; in a video, the first text subtitle is
    translated and added as a new track."""
    srts = [f for f in await _files(path) if f.lower().endswith(".srt")]
    if srts:
        for f in srts:
            await _translate_srt(f, f"{ospath.splitext(f)[0]}.{lang}.srt", lang)
        return path
    for video in await _videos(path):
        streams = await _probe(video)
        text_sub = next((st["index"] for st in streams if st.get("codec_type") == "subtitle"
            and st.get("codec_name") in ("subrip", "ass", "ssa", "mov_text", "webvtt", "text")), None)
        if text_sub is None:
            continue
        base, ext = ospath.splitext(video)
        src, dst = f"{base}.vt_src.srt", f"{base}.vt_tr.srt"
        if not await _run_ff(listener, ["-i", video, "-map", f"0:{text_sub}", "-c:s", "srt", src]):
            continue
        if await _translate_srt(src, dst, lang):
            n = sum(1 for st in streams if st.get("codec_type") == "subtitle")
            codec = "mov_text" if ext.lower() == ".mp4" else "srt"
            out = f"{base}.vt{ext}"
            cmd = ["-i", video, "-i", dst, "-map", "0", "-map", "1:0", "-c", "copy", f"-c:s:{n}", codec,
                   f"-metadata:s:s:{n}", f"language={lang}", f"-metadata:s:s:{n}", f"title=Translated ({lang})"]
            if not await _replace(listener, video, out, cmd + [out]) and ext.lower() != ".mkv":
                cmd[cmd.index(codec)] = "srt"
                await _replace(listener, video, f"{base}.vt.mkv", cmd + [f"{base}.vt.mkv"])
        for f in (src, dst):
            if await aiopath.exists(f):
                await aioremove(f)
    return path


async def run_video_tools(listener, path, sel):
    """Order: merge, remove, trim, extract, convert, owner tools, rename, screenshots.
    Returns the new path, or None when cancelled."""
    steps = [
        ("merge_video", lambda p: merge_videos(listener, p)),
        ("merge_audio", lambda p: _mux_extra(listener, p, "audio")),
        ("merge_subs", lambda p: _mux_extra(listener, p, "subs")),
        ("remove", lambda p: remove_streams(listener, p, sel["remove"])),
        ("trim", lambda p: trim_videos(listener, p, *sel["trim"])),
        ("extract", lambda p: extract_streams(listener, p, sel["extract"])),
        ("merge_all", lambda p: _mux_extra(listener, p, "audio")),
        ("merge_all", lambda p: _mux_extra(listener, p, "subs")),
        ("strip", lambda p: strip_metadata(listener, p)),
        ("async", lambda p: shift_streams(listener, p, "a", sel["async"])),
        ("ssync", lambda p: shift_streams(listener, p, "s", sel["ssync"])),
        ("chapters", lambda p: set_chapters(listener, p, sel["chapters"])),
        ("daudio", lambda p: default_audio(listener, p, sel["daudio"])),
        ("asplit", lambda p: split_audio(listener, p, sel["asplit"])),
        ("translate", lambda p: translate_subs(listener, p, sel["translate"])),
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
    if new_name := sel.get("rename"):
        try:
            path = await rename_output(path, new_name)
        except Exception as e:
            LOGGER.error(f"Video Tools rename failed: {e}")
    if count := sel.get("ss"):
        path = await make_sample_and_screenshots(listener, path, 0, count)
        if path is None or listener.suproc == "cancelled":
            return None
    return path
