#!/usr/bin/env python3
# Auto thumbnail from TMDB, ported from WZML-X wzv3 (bot/helper/ext_utils/tmdb_utils.py)
import re
from asyncio import sleep
from io import BytesIO
from os import path as ospath
from time import time
from urllib.parse import unquote

from aiofiles.os import makedirs
from aiohttp import ClientSession, ClientTimeout
from PIL import Image

from bot import LOGGER, config_dict
from bot.helper.ext_utils.bot_utils import sync_to_async


class _Resp:
    def __init__(self, status, data):
        self.status = status
        self.data = data


async def _get(client, url, params, headers):
    async with client.get(url, params=params, headers=headers) as r:
        data = await r.json(content_type=None) if r.status == 200 else {}
        return _Resp(r.status, data)


TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/multi"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/original"

_QUALITY_TAGS = re.compile(
    r"\b(?:\d{3,4}p|4k|x26[45]|h\.?26[45]|hevc|avc|xvid|divx|aac\d?|ac3|eac3|ddp?\d(?:\.\d)?"
    r"|dts(?:-hd)?|truehd|atmos|hdr\d*|10bit|8bit|web-?dl|web-?rip|blu-?ray|bd-?rip"
    r"|br-?rip|hd-?rip|dvd-?rip|hdts|cam-?rip|hdtv|remux|repack|esubs?|msubs?|subbed"
    r"|dubbed|dsnp|amzn|hmax|hotstar|mkv|mp4|m4v|avi|webm|mpe?g|rar|zip|7z|part\d+)\b",
    re.IGNORECASE,
)
_SITE_PREFIX = re.compile(
    r"^\W*(?:www\.)?[\w-]+\.(?:com|net|org|xyz|me|in|to|co|cc|info|tv|link|app|online"
    r"|site|club|work|icu|top|vip|pro|party|fun|cam|lol|sbs|ws)"
    r"(?:\s*[-–—]+\s*|\s+)",
    re.IGNORECASE,
)

_poster_cache = {}


def _tidy(title):
    title = re.sub(r"\s-+\s", " ", title)
    return re.sub(r"\s+", " ", title).strip(" -_.")


def _final_clean(title):
    base = re.sub(r"[\[\](){}]", " ", title)
    return _tidy(_QUALITY_TAGS.sub(" ", base)) or _tidy(base)


def clean_poster_title(raw_title):
    title = unquote(raw_title)
    title = re.sub(r"https?://\S+", " ", title)
    title = re.sub(r"\b(?:t|telegram)\.me/\S+", " ", title, flags=re.IGNORECASE)
    title = re.sub(r"\[[^\]]*\]", " ", title)
    title = re.sub(r"[\[\](){}]", " ", title)
    title = re.sub(r"\.\w{2,4}$", "", title)
    title = _SITE_PREFIX.sub("", title)
    title = re.sub(r"\bwww\S*", " ", title, flags=re.IGNORECASE)
    title = title.replace("_", " ")
    if _QUALITY_TAGS.search(title):
        title = re.sub(r"-\w+$", "", title)
    title = title.replace(".", " ")
    title = re.sub(r"\s+", " ", title).strip()

    for pattern in (
        r"(?<!\w)S0*\d{1,2}\s?E\d{1,3}(?!\w)",
        r"\bSeason\s+\d{1,2}\b",
        r"(?<!\w)S0*\d{1,2}(?!\w)",
        r"(?<!\w)(?:E|EP|EPISODE)\s?\d{1,4}(?!\w)",
    ):
        marker = re.search(pattern, title, re.IGNORECASE)
        if marker:
            head = title[: marker.start()].strip()
            tail = title[marker.end() :].strip()
            title = head if len(head) > 1 else tail
            return _final_clean(title), None

    years = list(re.finditer(r"\b(?:19|20)\d{2}\b", title))
    if years:
        last = years[-1]
        head = title[: last.start()].strip()
        tail = title[last.end() :].strip()
        return _final_clean(head if len(head) > 1 else tail), last.group(0)

    return _final_clean(title), None


def _pick_image(images, as_doc):
    backdrops = images.get("backdrops", [])
    posters = images.get("posters", [])
    en_backdrops = [i for i in backdrops if i.get("iso_639_1") == "en"]
    no_lang_backdrops = [i for i in backdrops if i.get("iso_639_1") is None]
    en_posters = [i for i in posters if i.get("iso_639_1") == "en"]
    no_lang_posters = [i for i in posters if i.get("iso_639_1") is None]

    if as_doc:
        order = [en_posters, no_lang_posters, posters, en_backdrops, no_lang_backdrops]
    else:
        order = [en_backdrops, no_lang_backdrops, backdrops, en_posters, posters]

    for group in order:
        if group:
            return group[0]["file_path"]
    return None


def _tmdb_token():
    return str(config_dict.get("TMDB_ACCESS_TOKEN") or "").strip()


async def get_tmdb_poster_link(title, year=None, as_doc=False):
    token = _tmdb_token()
    if not token:
        return None

    headers = {"accept": "application/json"}
    params = {
        "query": title,
        "include_adult": "false",
        "language": "en-US",
        "page": "1",
    }
    if len(token) < 50:
        params["api_key"] = token
    else:
        headers["Authorization"] = f"Bearer {token}"

    for attempt in range(3):
        try:
            async with ClientSession(timeout=ClientTimeout(total=15)) as client:
                resp = await _get(client, TMDB_SEARCH_URL, params, headers)
                if resp.status == 401:
                    LOGGER.warning("TMDb authentication failed, check TMDB_ACCESS_TOKEN")
                    return None
                if resp.status >= 500:
                    await sleep(2)
                    continue
                if resp.status != 200:
                    LOGGER.warning(f"TMDb returned {resp.status} for '{title}'")
                    return None

                results = [
                    r
                    for r in resp.data.get("results", [])
                    if r.get("media_type") != "person"
                ]
                if not results:
                    LOGGER.info(f"No TMDb results for '{title}'")
                    return None

                first = results[0]
                if year:
                    for result in results:
                        date = (
                            result.get("release_date")
                            or result.get("first_air_date")
                            or ""
                        )
                        if date.startswith(year):
                            first = result
                            break
                media_type = first.get("media_type", "movie")

                img_params = {"include_image_language": "en,null"}
                if len(token) < 50:
                    img_params["api_key"] = token
                img_resp = await _get(
                    client,
                    f"https://api.themoviedb.org/3/{media_type}/{first['id']}/images",
                    img_params,
                    headers,
                )
                if img_resp.status == 200:
                    path = _pick_image(img_resp.data, as_doc)
                    if path:
                        return f"{TMDB_IMAGE_URL}{path}"

                backdrop = first.get("backdrop_path")
                poster = first.get("poster_path")
                fallback = (poster or backdrop) if as_doc else (backdrop or poster)
                if fallback:
                    return f"{TMDB_IMAGE_URL}{fallback}"
                return None
        except Exception as e:
            LOGGER.warning(f"TMDb request failed ({attempt + 1}/3): {e}")
            await sleep(1)
    return None


def get_auto_cover(thumb):
    """Full quality cover saved next to an auto thumbnail."""
    if thumb and ospath.basename(thumb) == "auto_thumb.jpg":
        cover = ospath.join(ospath.dirname(thumb), "auto_cover.jpg")
        if ospath.exists(cover):
            return cover
    return None


async def get_auto_thumbnail(filename, as_doc=False):
    """Poster/backdrop from TMDB as a telegram ready jpg (max 320px, under
    200KB) plus the original image as auto_cover.jpg. None if not found."""
    if not _tmdb_token():
        return None
    title, year = clean_poster_title(filename)
    if len(title) < 2:
        return None
    key = (title, year, as_doc)
    poster_url = _poster_cache.get(key)
    if not poster_url:
        poster_url = await get_tmdb_poster_link(title, year, as_doc)
        if not poster_url:
            return None
        if len(_poster_cache) > 200:
            _poster_cache.clear()
        _poster_cache[key] = poster_url
    LOGGER.info(f"Auto thumbnail for '{title}': {poster_url}")
    try:
        async with ClientSession(timeout=ClientTimeout(total=60)) as client:
            async with client.get(poster_url) as r:
                if r.status != 200:
                    return None
                raw = await r.read()
        des_dir = ospath.join("Thumbnails", f"{time()}")
        await makedirs(des_dir, exist_ok=True)
        output = ospath.join(des_dir, "auto_thumb.jpg")
        cover = ospath.join(des_dir, "auto_cover.jpg")

        def _save():
            with Image.open(BytesIO(raw)) as img:
                img = img.convert("RGB")
                # cover: original resolution, telegram photo limit is 10MB
                if max(img.size) > 4096:
                    img.thumbnail((4096, 4096), Image.LANCZOS)
                img.save(cover, "JPEG", quality=95, optimize=True)
                # thumb: telegram allows max 320px and 200KB
                thumb = img.copy()
                thumb.thumbnail((320, 320), Image.LANCZOS)
                for quality in (95, 90, 85, 75):
                    thumb.save(output, "JPEG", quality=quality, optimize=True)
                    if ospath.getsize(output) < 200 * 1024:
                        break

        await sync_to_async(_save)
        return output
    except Exception as e:
        LOGGER.warning(f"Auto thumbnail download failed: {e}")
        return None
