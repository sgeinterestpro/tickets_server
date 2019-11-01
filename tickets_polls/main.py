"""
filename: main.py
datetime: 2019-04-19
author: muumlover
"""

import logging

from aiohttp import web

from base import setup_database, setup_email, setup_report, setup_task
from config import setup_config
from model import setup_model
from routes import setup_routes, setup_middleware

logging.basicConfig(
    format='%(levelname)s: %(asctime)s [%(pathname)s:%(lineno)d] %(message)s',
    level=logging.NOTSET
)

app = web.Application()
setup_config(app)
setup_routes(app)
setup_middleware(app)

setup_database(app)
setup_model(app)  # 依赖 database
setup_task(app)  # 依赖 database

setup_email(app)
setup_report(app)  # 依赖 email, database

host, port = app['config']['server']['host'], int(app['config']['server']['port'])
web.run_app(app, host=host, port=port)
