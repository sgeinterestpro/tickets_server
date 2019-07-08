"""
filename: main.py
datetime: 2019-04-19
author: muumlover
"""

import logging

from aiohttp import web

from config import setup_config
from u_database import setup_database
from routes import setup_routes, setup_middleware
from u_task import setup_task

logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                    level=logging.INFO)

app = web.Application()
setup_config(app)
setup_routes(app)
setup_middleware(app)
setup_database(app)
setup_task(app)  # 需要在数据库设置完成后设置
host, port = app['config']['server']['host'], int(app['config']['server']['port'])
web.run_app(app, host=host, port=port)
