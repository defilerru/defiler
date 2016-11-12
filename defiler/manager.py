import asyncio
from concurrent.futures import CancelledError
from collections import defaultdict, deque
import json

from defiler.connection import Connection
from defiler import twitch

POOL_INTERVAL = 1


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
        self.chat_data = defaultdict(
            lambda: deque([], int(cfg["chat"]["remember_lines"])))

    def stream_online_cb(self, stream):
        self.streams[stream.slug] = stream
        self.broadcast(stream.event_str)
        print("ONLINE", stream)

    def stream_offline_cb(self, stream):
        stream = self.streams.pop(stream.slug)
        print("OFFLINE", stream)

    async def start(self):
        from defiler import mysql
        self.db = mysql.DB()
        await self.db.connect(**dict(self.cfg["mysql"]))

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

    def new_connection(self, ws):
        connection = Connection(ws, self)
        self.connections[ws] = connection
        for stream in self.streams.values():
            connection.ws.send_str(stream.event_str)
        user_event = json.dumps(["USER_ONLINE", {"nickname": connection.username}])
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
