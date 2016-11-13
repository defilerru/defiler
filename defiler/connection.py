import json

PUBLIC_METHODS = {"login", "logout", "chat", "join", "leave"}


class Connection:

    def __init__(self, ws, manager, uid, nickname, sid):
        self.ws = ws
        self.manager = manager
        self.uid = uid
        self.nickname = nickname
        self.sid = sid

    def get_api_method(self, name):
        if name in PUBLIC_METHODS:
            return getattr(self, name)

    async def login(self, username, password):
        gas = await self.manager.db.check_auth(username, password)
        if not gas:
            return ["AUTH", {"success": False}]
        self.nickname = username
        return ["AUTH", {"success": True, "nickname": self.nickname, "uid": None}]

    async def logout(self):
        await self.manager.db.delete_session(self.sid)
        self.uid = None
        self.nickname = None
        self.sid = None
        return ["LOGOUT", {}]

    def join(self, channel):
        self.manager.join(channel, self)

    def leave(self, channel):
        self.manager.leave(channel, self)

    def send_json(self, data):
        try:
            self.ws.send_str(json.dumps(data))
        except Exception as ex:
            print(ex)

    def chat(self, channel, message):
        data = json.dumps(["CHAT", {"channel": channel,
                                    "nickname": self.nickname,
                                    "message": message}])
        self.manager.multicast(channel, data)
