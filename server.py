from defiler import views
from aiohttp import web


def init(argv):
    app = web.Application()
    app.router.add_get('/', views.index)
    app.router.add_get('/wsapi', views.wsapi)
    return app
