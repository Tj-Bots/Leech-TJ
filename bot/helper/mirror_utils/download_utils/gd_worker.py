#!/usr/bin/env python3
"""Public Google Drive links without token.pickle: GDRIVE_WORKER (our Cloudflare worker)
lists files and folders and streams them, so no Google login is needed."""
from os import path as ospath
from urllib.parse import quote

from aiohttp import ClientSession

from bot import LOGGER, config_dict


def worker_url():
    return (config_dict.get("GDRIVE_WORKER") or "").strip().rstrip("/")


def drive_ready():
    """token.pickle or service accounts: the normal Drive download works."""
    return config_dict.get("USE_SERVICE_ACCOUNTS") or ospath.exists("token.pickle")


async def _api(session, target):
    async with session.get(f"{worker_url()}/api", params={"url": target}, timeout=60) as resp:
        data = await resp.json(content_type=None)
    if not data.get("ok"):
        raise Exception(data.get("error") or f"HTTP {resp.status}")
    return data


async def worker_details(link):
    """A direct link (one file) or a details dict for add_direct_download (a folder)."""
    async with ClientSession() as session:
        top = await _api(session, link)
        if top.get("type") != "folder":
            return top.get("direct") or f"{worker_url()}/dl/{top['id']}/{quote(top['name'])}"
        details = {"contents": [], "title": top["name"], "total_size": 0}

        async def walk(folder, rel, depth):
            for item in folder.get("items", []):
                if item.get("type") == "folder":
                    if depth < 20:
                        sub = await _api(session, item["id"])
                        await walk(sub, ospath.join(rel, item["name"]), depth + 1)
                    continue
                details["contents"].append({
                    "path": rel,
                    "filename": item["name"],
                    "url": item.get("direct") or f"{worker_url()}/dl/{item['id']}/{quote(item['name'])}",
                })
                details["total_size"] += int(item.get("size") or 0)

        await walk(top, top["name"], 0)
        LOGGER.info(f"GDrive worker: {len(details['contents'])} file(s) in {top['name']}")
        return details
