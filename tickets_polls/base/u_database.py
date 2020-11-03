"""
filename: u_database.py
datetime: 2019-04-22
author: muumlover
"""
from urllib.parse import quote_plus

from aiohttp.abc import Application
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient


def setup_database(app: Application) -> None:
    if 'config' not in app:
        raise Exception('需要初始化配置参数')
    conf = app['config']
    uri = 'mongodb://'
    if conf['database']['user'] != '':
        uri += '{}:{}@'.format(quote_plus(conf['database']['user']), quote_plus(conf['database']['pass']))
    uri += '{}:{}'.format(quote_plus(conf['database']['host']), conf['database']['port'])
    uri += '/{}'.format(quote_plus(conf['database']['name']))
    client = AsyncIOMotorClient(uri)
    app['db'] = client.get_database(quote_plus(conf['database']['name']))
    config_database(uri, quote_plus(conf['database']['name']))


def config_database(uri: str, db_name: str) -> None:
    client = MongoClient(uri)
    db = client.get_database(db_name)
    # db.captcha.create_index('expire_time', expireAfterSeconds=3600)
    # noinspection PyBroadException

    # 设置验证码表数据过期时间
    try:
        db.captcha.drop_index('expire_time_1')
    except Exception:
        pass
    db.captcha.create_index('expire_time', expireAfterSeconds=600)

    client.close()
    pass
