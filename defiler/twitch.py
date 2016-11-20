import asyncio
import json
import urllib.parse
import logging
from concurrent.futures import CancelledError
import aiohttp

LOG = logging.getLogger(__name__)
ADD_STREAM_QUERY = "INSERT INTO streams_twitch(slug, name) VALUES (%s, %s)"
API_URL = "https://api.twitch.tv/kraken"
STREAMS_CHECK_URL = API_URL + "/streams?channel=%s&client_id=%s"


MAX_URL_LEN = 1024


class Stream:
    viewers = 0

    def __init__(self, data):
        """
        :param dict data: stream data returned from twitch API
        """
        self.slug = data["channel"]["name"]
        self._data = data
        self.info = {
            "provider": "twitch",
            "slug": self.slug,
            "name": data["channel"]["display_name"],
            "preview": data["preview"]["medium"],
            "game": data["channel"]["game"],
            "viewers": data["viewers"],
            "display_name": data["channel"]["display_name"],
            "status": data["channel"]["status"],
            "language": data["channel"]["broadcaster_language"],
        }
        self.event_str = json.dumps(["STREAM", self.info])

    def __str__(self):
        return "<Twitch stream '%s'>" % self.slug

    def update(self, status, game, preview):
        updated = {}
        if status != self.status:
            self.status = updated["status"] = status


class Checker:
    provider = "twitch"

    def __init__(self, manager):
        self.manager = manager
        self._online = {}
        self.delay = int(self.manager.cfg["twitch"]["delay"])
        self._all_streams = []
        self._slices = []
        self._find_streams_url = API_URL + "/streams?" + urllib.parse.urlencode({
            "game": "StarCraft: Brood War",
            "client_id": self.manager.cfg["twitch"]["id"],
            "stream_type": "live",
        })

    def _add_stream(self, name):
        self._all_streams.append(name)
        if self._slices:
            self._slices = []

    def _get_slices(self):
        if self._slices:
            return self._slices
        csv = ""
        for slug in self._all_streams:
            csv += slug
            if len(csv) > MAX_URL_LEN:
                self._slices.append(csv)
                csv = ""
            else:
                csv += ","
        if csv:
            self._slices.append(csv[:-1])
        return self._slices

    async def _find_streams(self):
        while 1:
            async with aiohttp.get(self._find_streams_url) as r:
                streams = await r.json()
                for s in streams["streams"]:
                    slug = s["channel"]["name"]
                    if slug not in self._all_streams:
                        self._add_stream(slug)
                break
                # TODO: see next page

    async def run(self):
        while 1:
            try:
                await asyncio.sleep(self.delay)
                await self._find_streams()
                await self._check_streams()
            except CancelledError:
                LOG.info("Checker cancelled")
                return
            except Exception as ex:
                LOG.exception("Error in check loop")

    async def _check_streams(self):
        online = set()
        for csv in self._get_slices():
            url = STREAMS_CHECK_URL % (csv, self.manager.cfg["twitch"]["id"])
            await asyncio.sleep(self.delay)
            while 1:
                r = await aiohttp.get(url)
                if r.status == 200 and r.headers["content-type"] == "application/json":
                    break
                else:
                    LOG.info("Error checking stream status %s" % r)
                await asyncio.sleep(2)
            data = await r.json()
            for stream in data["streams"]:
                slug = stream["channel"]["name"]
                online.add(slug)
                if slug not in self._online:
                    stream = Stream(stream)
                    self._online[slug] = stream
                    self.manager.stream_online_cb(stream)
        for slug in set(self._online.keys()) - online:
            self._online.pop(slug)
            self.manager.stream_offline_cb(slug)
