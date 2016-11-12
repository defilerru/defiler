import asyncio
import json
import pkgutil

import aiohttp


def index(request):
    return aiohttp.web.Response(status=200, content_type="text/html",
                                body=pkgutil.get_data("defiler.static", "index.html"))


async def wsapi(request):
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    connection = request.app["defiler"].new_connection(ws)
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
    pass


async def oauth2_handle(request):
    pass
