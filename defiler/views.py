import asyncio
import json
import pkgutil

import aiohttp


def index(request):
    return aiohttp.web.Response(status=200, content_type="text/html",
                                body=pkgutil.get_data("defiler.static",
                                                      "index.html"))


async def wsapi(request):
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    connection = await request.app["defiler"].new_connection(ws, request)
    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                method, kwargs = json.loads(msg.data)
                method = connection.get_api_method(method)
                if asyncio.iscoroutinefunction(method):
                    res = await method(**kwargs)
                else:
                    res = method(**kwargs)
                if res is not None:
                    connection.send_json(res)
            else:
                print("unknown msg type", msg, msg.type)
    finally:
        request.app["defiler"].close_connection(ws)
    return ws


async def oauth2_init(request):
    return aiohttp.web.HTTPFound(request.app["defiler"].oauth2.get_url())


async def oauth2_handle(request):
    manager = request.app["defiler"]
    token = await manager.oauth2.get_token(
        request.GET["state"].encode("ascii"), request.GET["code"])
    twitch_username = await request.app["defiler"].oauth2.get_username(token)
    old_uid = await manager.get_session_user(request)
    response = aiohttp.web.HTTPFound("/")
    uid, nickname = await manager.db.get_or_create_user_by_twitch(twitch_username)
    await manager.set_sesssion_user(response, uid, nickname)
    return response
