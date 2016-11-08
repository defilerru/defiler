import json

PUBLIC_METHODS = {"login", "logout", "chat", "join", "leave"}


class Session:

    def __init__(self, ws, manager):
        self.ws = ws
        self.manager = manager
        self.username = str(id(ws))

    def get_api_method(self, name):
        if name in PUBLIC_METHODS:
            return getattr(self, name)

    async def login(self, username, password):
        gas = await self.manager.db.check_auth(username, password)
        if not gas:
            return {"event": "LOGIN", "status": "UNAUTHORIZED"}
        self.username = username
        return {"event": "LOGIN", "status": "OK", "token": "123", "username": username}

    def logout(self):
        self.username = str(id(self.ws))
        return {"event": "LOGOUT", "status": "OK"}

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
                                    "nickname": self.username,
                                    "message": message}])
        self.manager.multicast(channel, data)
