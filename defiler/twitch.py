import asyncio
import json

import aiohttp

ADD_STREAM_QUERY = "INSERT INTO streams_twitch(slug, name) VALUES (%s, %s)"
API_URL = "https://api.twitch.tv/kraken"
STREAMS_CHECK_URL = API_URL + "/streams?channel=%s&client_id=%s"
MAX_URL_LEN = 1024


class Stream:
    viewers = 0

    def __init__(self, name, data):
        """
        :param dict data: stream data returned from twitch API
        """
        self.slug = data["channel"]["name"]
        self._data = data
        self.info = {
            "provider": "twitch",
            "slug": self.slug,
            "name": name,
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
        self._new_streams = asyncio.Queue()
        self._online = {}
        self._names = {}
        self.delay = int(self.manager.cfg["twitch"]["delay"])

    def add_stream(self, data):
        try:
            self.manager.db.execute(ADD_STREAM_QUERY, data["slug"], data["name"])
        except Exception as ex:
            raise

    async def run(self):
        rows = await self.manager.db.get_streams(self.provider)
        slices = []
        csv = ""
        for row in rows:
            self._names[row[0]] = row[1]
            csv += row[0]
            if len(csv) > MAX_URL_LEN:
                slices.append(csv)
                csv = ""
            else:
                csv += ","
        if csv:
            slices.append(csv[:-1])

        while 1:
            try:
                await self._check_streams(slices)
            except Exception as ex:
                print(ex)
                raise

    async def _check_streams(self, slices):
        online = set()
        for csv in slices:
            url = STREAMS_CHECK_URL % (csv, self.manager.cfg["twitch"]["id"])
            await asyncio.sleep(self.delay)
            while 1:
                r = await aiohttp.get(url)
                if r.status == 200 and r.headers["content-type"] == "application/json":
                    break
                else:
                    print(r.status)
                await asyncio.sleep(2)
            data = await r.json()
            for stream in data["streams"]:
                slug = stream["channel"]["name"]
                online.add(slug)
                if slug not in self._online:
                    stream = Stream(self._names[slug], stream)
                    self._online[slug] = stream
                    self.manager.stream_online_cb(stream)
        for slug in set(self._online.keys()) - online:
            self._online.pop(slug)
            self.manager.stream_offline_cb(slug)
