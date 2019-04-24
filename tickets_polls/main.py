from aiohttp import web

from config import setup_config
from database import setup_database
from routes import setup_routes

app = web.Application()
setup_config(app)
setup_routes(app)
setup_database(app)
host, port = app['config']['server']['host'], int(app['config']['server']['port'])
web.run_app(app, host=host, port=port)
