import os
import urllib.parse
import base64
import collections

import aiohttp

TWITCH_API_URL = "https://api.twitch.tv/kraken"
TWITCH_AUTH_URL = TWITCH_API_URL + "/oauth2/authorize?"
TWITCH_TOKEN_URL = TWITCH_API_URL + "/oauth2/token"
TWITCH_USER_URL = TWITCH_API_URL + "/user"


class Twitch:

    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.states = collections.deque(maxlen=64)

    def get_url(self):
        state = base64.b32encode(os.urandom(15))
        self.states.append(state)
        return TWITCH_AUTH_URL + urllib.parse.urlencode({
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
        })

    async def get_token(self, state, code):
        self.states.remove(state)
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "code": code,
            "state": state,
        }
        async with await aiohttp.post(TWITCH_TOKEN_URL, data=data) as r:
            data = await r.json()
            return data["access_token"]

    async def get_username(self, token):
        headers = {"Authorization": "OAuth " + token}
        async with await aiohttp.get(TWITCH_API_URL, headers=headers) as r:
            data = await r.json()
            return data["token"]["user_name"]
