"""
filename: main.py
datetime: 2019-04-19
author: muumlover
"""

from aiohttp import web

from config import setup_config
from database import setup_database
from routes import setup_routes, setup_middleware

app = web.Application()
setup_config(app)
setup_routes(app)
setup_database(app)
setup_middleware(app)
host, port = app['config']['server']['host'], int(app['config']['server']['port'])
web.run_app(app, host=host, port=port)
