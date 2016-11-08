import aiohttp

import abc
import asyncio
import re


POOL_INTERVAL = 1
USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0"
AFREECA_CHECK_URL = "http://live.afreecatv.com:8079/app/index.cgi?szBjId=%s"
AFREECA_TN_RE =  re.compile(r'.+broadImg.+(https?://.+)\?')
TWITCH_CHECK_URL = 'https://static-cdn.jtvnw.net/previews-ttv/live_user_%s-240x180.jpg'
TWITCH_CHECK_URL_ = 'https://api.twitch.tv/kraken/streams?channel=%s&client_id=%s'
# channel=csv
AFREECA_HEADERS = {"User-Agent": USER_AGENT}


class Checker(abc.ABC):

    def __init__(self, config, manager):
        self._streams = []
        self.manager = manager
        self.new_streams = asyncio.Queue()
        self.config = config

    @abc.abstractmethod
    async def checker(self):
        pass


class Stream(abc.ABC):

    def __init__(self, provider, slug, name):
        self.provider = provider
        self.slug = slug
        self.name = name
        self.status = None
        self.game = None

    @abc.abstractmethod
    def update(self, status, game, preview):
        """Update state and return dict with updated values"""
        pass


class Stream_:
    preview = None
    online = False

    def __init__(self, provider, slug, name):
        self.provider = provider
        self.slug = slug
        self.checker = getattr(self, "_check_%s" % provider)

    def get_event(self):
        return {
            "event": "STREAM",
            "online": self.online,
            "slug": self.slug,
            "provider": self.provider,
            "name": "FIXME",
            "preview": self.preview,
        }

    def __str__(self):
        return "<Stream %s.%s.%s>" % (self.slug, self.provider, self.online)

    async def _check_afreeca(self):
        url = AFREECA_CHECK_URL % self.slug
        async with aiohttp.request("GET", url, headers=AFREECA_HEADERS) as resp:
            text = await resp.text()
            for line in text.splitlines():
                m = AFREECA_TN_RE.match(line)
                if m:
                    tn_url = m.group(1)
                    if "default" in tn_url:
                        return False
                    self.preview = tn_url
                    return True

    async def _check_twitch(self):
        url = TWITCH_CHECK_URL % self.slug
        self.preview = url
        async with aiohttp.request('GET', url, allow_redirects=False) as resp:
            return resp.status == 200

    async def check(self):
        old_online = self.online
        self.online = await self.checker()
        return self.online != old_online
