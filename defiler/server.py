from defiler import manager
from defiler import views

from aiohttp import web

import configparser
import os


async def startup(app):
    config = configparser.ConfigParser()
    config.read(os.environ.get("DEFILER_INI", "/etc/defiler.ini"))
    app["defiler"] = manager.Manager(app, config)
    await app["defiler"].start()


async def cleanup(app):
    await app["defiler"].stop()


def app(argv):
    app = web.Application()
    app.router.add_get('/', views.index)
    app.router.add_get('/wsapi', views.wsapi)
    app.router.add_post('/login/twitch', views.oauth2_init)
    app.router.add_get('/oauth2/twitch', views.oauth2_handle)
    app.router.add_static('/static', 'defiler/static')
    app.on_startup.append(startup)
    app.on_cleanup.append(cleanup)
    return app
