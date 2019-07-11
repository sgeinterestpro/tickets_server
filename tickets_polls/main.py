"""
filename: main.py
datetime: 2019-04-19
author: muumlover
"""

import logging

from aiohttp import web

from config import setup_config
from routes import setup_routes, setup_middleware
from u_database import setup_database
from u_email import setup_email
from u_report import setup_report
from u_task import setup_task

logging.basicConfig(
    format='%(levelname)s: %(asctime)s [%(pathname)s:%(lineno)d] %(message)s',
    level=logging.NOTSET
)

app = web.Application()
setup_config(app)
setup_routes(app)
setup_middleware(app)

setup_database(app)
setup_task(app)  # 依赖 database

setup_email(app)
setup_report(app)  # 依赖 email, database

host, port = app['config']['server']['host'], int(app['config']['server']['port'])
web.run_app(app, host=host, port=port)
