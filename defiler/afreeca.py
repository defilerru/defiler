import asyncio
import re
import json

import aiohttp

CHECK_URL_TPL = "http://live.afreecatv.com:8079/app/index.cgi?szBjId=%s"
USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0"
HEADERS = {"User-Agent": USER_AGENT}
TN_RE =  re.compile(r'.+broadImg.+(https?://.+)\?')


class Stream:
    viewers = 0

    def __init__(self, slug, name, tn):
        self.slug = slug
        self.name = name
        self.info = {
            "slug": slug,
            "name": name,
            "preview": tn,
            "provider": "afreeca",
        }
        self.event_str = json.dumps(["STREAM", self.info])


class Checker:
    provider = "afreeca"

    def __init__(self, manager):
        self.manager = manager
        self.delay = int(self.manager.cfg["twitch"]["delay"])
        self._online = {}

    async def run(self):
        rows = await self.manager.db.get_streams(self.provider)
        while 1:
            for slug, name in rows:
                online, tn_url = await self._check_stream(slug)
                if online:
                    if slug not in self._online:
                        stream = Stream(slug, name, tn_url)
                        self._online[slug] = stream
                        self.manager.stream_online_cb(stream)
                else:
                    if slug in self._online:
                        self._online.pop(slug)
                        self.manager.stream_offline_cb(slug)
                await asyncio.sleep(self.delay)

    async def _check_stream(self, slug):
        async with aiohttp.get(CHECK_URL_TPL % slug, headers=HEADERS) as resp:
            text = await resp.text()
            for line in text.splitlines():
                m = TN_RE.match(line)
                if m:
                    tn_url = m.group(1)
                    if "default" in tn_url:
                        return (False, None)
                    return (True, tn_url)
