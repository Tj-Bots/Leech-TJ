#!/usr/bin/env python3
# PixelDrain, BuzzHeavier, DevUploads and VikingFile uploaders, ported from
# WZML-X wzv3 (bot/helper/mirror_leech_utils/uphoster_utils) to the DDL engine.
from json import loads as json_loads
from os import path as ospath, walk

from aiofiles.os import path as aiopath
from aiohttp import BasicAuth, ClientSession, ClientTimeout, FormData

from bot import LOGGER
from bot.helper.ext_utils.bot_utils import sync_to_async
from bot.helper.ext_utils.telegraph_helper import telegraph

UPLOAD_TIMEOUT = ClientTimeout(total=None, sock_read=600)


def split_api(api):
    """'token folder' -> (token, folder)"""
    parts = str(api or "").split(maxsplit=1)
    return (parts[0] if parts else ""), (parts[1].strip() if len(parts) > 1 else "")


def extract_id(response):
    if isinstance(response, str):
        try:
            response = json_loads(response)
        except Exception:
            return response.strip().strip('"')
    if isinstance(response, dict):
        if "id" in response:
            return response["id"]
        if isinstance(response.get("data"), dict) and "id" in response["data"]:
            return response["data"]["id"]
    return response


async def _list_files(path):
    files = []
    for root, _, fnames in await sync_to_async(walk, path):
        files.extend(ospath.join(root, f) for f in sorted(fnames))
    return files


async def _telegraph_links(title, links):
    content = "".join(
        f'<p>{i}. <a href="{url}">{name}</a></p>'
        for i, (name, url) in enumerate(links, 1)
    )
    page = await telegraph.create_page(title=title, content=content)
    return f"https://telegra.ph/{page['path']}"


class _Host:
    NAME = ""

    def __init__(self, dluploader, api):
        self.dluploader = dluploader
        self.token, self.folder = split_api(api)

    def _reader(self, file_path):
        from bot.helper.mirror_utils.upload_utils.ddlEngine import ProgressFileReader

        self.dluploader.last_uploaded = 0
        return ProgressFileReader(
            filename=file_path, read_callback=self.dluploader.progress_callback
        )

    async def upload(self, file_path):
        if await aiopath.isfile(file_path):
            self.dluploader.total_files = 1
            return await self.upload_file(file_path)
        links = []
        for f_path in await _list_files(file_path):
            if self.dluploader.is_cancelled:
                return None
            if link := await self.upload_file(f_path):
                links.append((ospath.basename(f_path), link))
                self.dluploader.total_files += 1
        if not links:
            raise Exception(f"{self.NAME}: no files uploaded")
        self.dluploader.total_folders = 1
        if len(links) == 1:
            return links[0][1]
        return await self.folder_link(ospath.basename(file_path), links)

    async def folder_link(self, title, links):
        return await _telegraph_links(title, links)


class PixelDrain(_Host):
    NAME = "PixelDrain"
    API = "https://pixeldrain.com/api/"

    async def upload_file(self, file_path):
        name = ospath.basename(file_path).replace(" ", ".")
        auth = BasicAuth("", self.token) if self.token else None
        with self._reader(file_path) as file:
            async with ClientSession(auth=auth, timeout=UPLOAD_TIMEOUT) as session:
                async with session.put(f"{self.API}file/{name}", data=file) as resp:
                    res = await resp.json(content_type=None)
                    if resp.status in (200, 201) and res.get("id"):
                        return f"https://pixeldrain.com/u/{res['id']}"
                    raise Exception(f"PixelDrain: {res.get('message', resp.status)}")

    async def folder_link(self, title, links):
        if not self.token:
            return await _telegraph_links(title, links)
        files = [{"id": url.rsplit("/", 1)[-1], "description": n} for n, url in links]
        async with ClientSession(auth=BasicAuth("", self.token)) as session:
            async with session.post(
                f"{self.API}list", json={"title": title, "files": files}
            ) as resp:
                res = await resp.json(content_type=None)
                if res.get("success") and res.get("id"):
                    return f"https://pixeldrain.com/l/{res['id']}"
        return await _telegraph_links(title, links)


class BuzzHeavier(_Host):
    NAME = "BuzzHeavier"
    API = "https://buzzheavier.com/api/"
    UPLOAD = "https://w.buzzheavier.com/"

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    async def _root_id(self):
        async with ClientSession() as session:
            async with session.get(f"{self.API}account", headers=self._headers()) as r:
                if r.status == 200:
                    res = await r.json(content_type=None)
                    if isinstance(res, dict):
                        if res.get("rootDirectoryId"):
                            return res["rootDirectoryId"]
                        data = res.get("data")
                        if isinstance(data, dict) and data.get("rootDirectoryId"):
                            return data["rootDirectoryId"]
                elif r.status in (401, 403):
                    raise Exception("BuzzHeavier: invalid API token!")
        return None

    async def upload_file(self, file_path, parent=""):
        name = ospath.basename(file_path).replace(" ", ".")
        parent = parent or self.folder or await self._root_id() or ""
        url = f"{self.UPLOAD}{parent}/{name}" if parent else f"{self.UPLOAD}{name}"
        with self._reader(file_path) as file:
            async with ClientSession(timeout=UPLOAD_TIMEOUT) as session:
                async with session.put(url, data=file, headers=self._headers()) as r:
                    text = await r.text()
                    if r.status not in (200, 201):
                        raise Exception(f"BuzzHeavier: HTTP {r.status} {text[:200]}")
        file_id = str(extract_id(text)).strip()
        if not file_id or "{" in file_id:
            raise Exception(f"BuzzHeavier: bad response {text[:200]}")
        return file_id if file_id.startswith("http") else f"https://buzzheavier.com/{file_id}"

    async def upload(self, file_path):
        if not self.token:
            raise Exception("BuzzHeavier: API token not set!")
        if await aiopath.isfile(file_path):
            self.dluploader.total_files = 1
            return await self.upload_file(file_path)
        # keep the folder structure on BuzzHeavier
        parent = self.folder or await self._root_id()
        if not parent:
            raise Exception("BuzzHeavier: can't get root folder id")
        folder_ids = {}

        async def make_folder(parent_id, name):
            async with ClientSession() as session:
                async with session.post(
                    f"{self.API}fs/{parent_id}", json={"name": name}, headers=self._headers()
                ) as r:
                    if r.status not in (200, 201):
                        raise Exception(f"BuzzHeavier: create folder failed {await r.text()}")
                    return extract_id(await r.json(content_type=None))

        main_id = await make_folder(parent, ospath.basename(file_path))
        folder_ids["."] = main_id
        for root, dirs, files in await sync_to_async(walk, file_path):
            rel = ospath.relpath(root, file_path)
            current = folder_ids.get(rel, main_id)
            for sub in dirs:
                folder_ids[sub if rel == "." else ospath.join(rel, sub)] = (
                    await make_folder(current, sub)
                )
                self.dluploader.total_folders += 1
            for f in sorted(files):
                if self.dluploader.is_cancelled:
                    return None
                await self.upload_file(ospath.join(root, f), current)
                self.dluploader.total_files += 1
        return f"https://buzzheavier.com/{main_id}"


class DevUploads(_Host):
    NAME = "DevUploads"

    async def _server(self):
        async with ClientSession() as session:
            async with session.get(
                f"https://devuploads.com/api/upload/server?key={self.token}"
            ) as r:
                res = await r.json(content_type=None)
                if res.get("status") == 200:
                    return res.get("sess_id"), res.get("result")
        raise Exception("DevUploads: invalid API key or no upload server!")

    async def upload(self, file_path):
        if not self.token:
            raise Exception("DevUploads: API key not set!")
        self._sess, self._url = await self._server()
        return await super().upload(file_path)

    async def upload_file(self, file_path):
        with self._reader(file_path) as file:
            data = FormData()
            data.add_field("sess_id", self._sess)
            data.add_field("utype", "reg")
            data.add_field("file", file, filename=ospath.basename(file_path))
            async with ClientSession(timeout=UPLOAD_TIMEOUT) as session:
                async with session.post(self._url, data=data) as r:
                    res = await r.json(content_type=None)
        if isinstance(res, list):
            res = res[0] if res else {}
        code = res.get("file_code")
        if not code:
            raise Exception(f"DevUploads: {res.get('message', res)}")
        if self.folder:
            try:
                async with ClientSession() as session:
                    await session.get(
                        "https://devuploads.com/api/file/set_folder"
                        f"?key={self.token}&file_code={code}&fld_id={self.folder}"
                    )
            except Exception as e:
                LOGGER.warning(f"DevUploads set folder failed: {e}")
        return f"https://devuploads.com/{code}"


class VikingFile(_Host):
    NAME = "VikingFile"
    API = "https://vikingfile.com/api"

    async def upload_file(self, file_path):
        if not getattr(self, "_srv", None):
            async with ClientSession() as session:
                async with session.get(f"{self.API}/get-server") as r:
                    res = await r.json(content_type=None)
                    self._srv = res.get("server") or "https://upload.vikingfile.com"
        with self._reader(file_path) as file:
            data = FormData()
            data.add_field("file", file, filename=ospath.basename(file_path))
            data.add_field("user", self.token or "")
            if self.folder:
                data.add_field("path", self.folder)
            async with ClientSession(timeout=UPLOAD_TIMEOUT) as session:
                async with session.post(self._srv, data=data) as r:
                    res = await r.json(content_type=None)
        if url := res.get("url"):
            return url
        raise Exception(f"VikingFile: {res}")


EXTRA_HOSTS = {
    "pixeldrain": PixelDrain,
    "buzzheavier": BuzzHeavier,
    "devuploads": DevUploads,
    "vikingfile": VikingFile,
}
