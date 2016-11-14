import asyncio
import base64
from concurrent.futures import CancelledError
from collections import defaultdict, deque
import json
import os

from defiler.connection import Connection
from defiler import afreeca
from defiler import twitch
from defiler import oauth2

POOL_INTERVAL = 1
GET_USER_QUERY = ("SELECT user_id, nickname, id FROM sessions WHERE id=%s "
                  "AND created > (NOW() - INTERVAL 30 DAY)")


class Manager:

    def __init__(self, app, cfg):
        """
        :param aiohttp.web.Application app: app
        :param ConfigParser cfg: defiler.ini
        """
        self.app = app
        self.cfg = cfg
        self.connections = {}
        self.channel_connection_map = defaultdict(set)
        self.connection_channel_map = defaultdict(set)
        self.streams = {}
        self.oauth2 = oauth2.Twitch(cfg["twitch"]["id"],
                                    cfg["twitch"]["secret"],
                                    cfg["defiler"]["base_url"] + "/oauth2/twitch")
        self.cookie_name = self.cfg["defiler"]["cookie_name"]
        self.chat_data = defaultdict(
            lambda: deque([], int(cfg["chat"]["remember_lines"])))

    async def get_session_user(self, request):
        """
        :returns tuple: (uid, nickname, sid)
        """
        sid = request.cookies.get(self.cookie_name)
        if sid is None:
            return
        user = await self.db.execute(GET_USER_QUERY, (sid, ))
        if user:
            return user[0]

    async def set_sesssion_user(self, response, uid, nickname):
        sid = base64.b64encode(os.urandom(15)).decode("ascii")
        await self.db.create_session(sid, uid, nickname)
        response.set_cookie(self.cookie_name, sid)

    def stream_online_cb(self, stream):
        self.streams[stream.slug] = stream
        self.broadcast(stream.event_str)
        print("ONLINE", stream)

    def stream_offline_cb(self, slug):
        stream = self.streams.pop(slug)
        print("OFFLINE", stream)

    async def start(self):
        from defiler import mysql
        self.db = mysql.DB()
        await self.db.connect(**dict(self.cfg["mysql"]))

        self.afreeca = afreeca.Checker(self)
        self.afreeca_checker = self.app.loop.create_task(self.afreeca.run())
        self.twitch = twitch.Checker(self)
        self.twitch_checker = self.app.loop.create_task(self.twitch.run())

    async def stop(self):
        for connection in self.connections.values():
            await connection.close()
        self.twitch_checker.cancel()
        try:
            await self.twitch_checker
        except CancelledError:
            pass

    async def new_connection(self, ws, request):
        user = await self.get_session_user(request)
        if user:
            uid, nickname, sid = user
        else:
            uid = nickname = sid = None
        connection = Connection(ws, self, uid, nickname, sid)
        if nickname is None:
            connection.send_json(["LOGOUT", {}])
        else:
            connection.send_json(["AUTH", {"success": True, "uid": uid, "nickname": nickname}])
        self.connections[ws] = connection
        for stream in self.streams.values():
            connection.ws.send_str(stream.event_str)
        user_event = json.dumps(["USER_ONLINE", {"nickname": connection.nickname}])
        for s in self.connections.values():
            s.ws.send_str(user_event)

        for user in self.channel_connection_map[()]:
            connection.send_json()
        return connection

    def close_connection(self, ws):
        connection = self.connections.pop(ws)
        for channel in self.connection_channel_map.pop(connection, []):
            self.channel_connection_map[channel].remove(connection)

    def join(self, channel, connection):
        self.channel_connection_map[channel].add(connection)
        self.connection_channel_map[connection].add(channel)
        for message in self.chat_data[channel]:
            connection.ws.send_str(message)

    def leave(self, channel, connection):
        self.channel_connection_map[channel].remove(connection)
        self.connection_channel_map[connection].remove(channel)

    def multicast(self, channel, message):
        self.chat_data[channel].append(message)
        for connection in self.channel_connection_map[channel]:
            connection.ws.send_str(message)

    def broadcast(self, message):
        for connection in self.connections.values():
            connection.ws.send_str(message)
