import asyncio
from concurrent.futures import CancelledError
from collections import defaultdict, deque
import json

from defiler.session import Session
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
        self.sessions = {}
        self.channel_session_map = defaultdict(set)
        self.session_channel_map = defaultdict(set)
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
        for session in self.sessions.values():
            await session.close()
        self.twitch_checker.cancel()
        try:
            await self.twitch_checker
        except CancelledError:
            pass

    def new_session(self, ws):
        session = Session(ws, self)
        self.sessions[ws] = session
        for stream in self.streams.values():
            session.ws.send_str(stream.event_str)
        user_event = json.dumps(["USER_ONLINE", {"nickname": session.username}])
        for s in self.sessions.values():
            s.ws.send_str(user_event)

        for user in self.channel_session_map[()]:
            session.send_json()
        return session

    def close_session(self, ws):
        session = self.sessions.pop(ws)
        for channel in self.session_channel_map.pop(session, []):
            self.channel_session_map[channel].remove(session)

    def join(self, channel, session):
        self.channel_session_map[channel].add(session)
        self.session_channel_map[session].add(channel)
        for message in self.chat_data[channel]:
            session.ws.send_str(message)

    def leave(self, channel, session):
        self.channel_session_map[channel].remove(session)
        self.session_channel_map[session].remove(channel)

    def multicast(self, channel, message):
        self.chat_data[channel].append(message)
        for session in self.channel_session_map[channel]:
            session.ws.send_str(message)

    def broadcast(self, message):
        for session in self.sessions.values():
            session.ws.send_str(message)
