"""
filename: u_database.py
datetime: 2019-04-22
author: muumlover
"""
from urllib.parse import quote_plus

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient


def setup_database(app):
    conf = app['config']
    uri = 'mongodb://'
    if conf['database']['user'] != '':
        uri += '{}:{}@'.format(quote_plus(conf['database']['user']), quote_plus(conf['database']['pass']))
    uri += '{}:{}'.format(quote_plus(conf['database']['host']), quote_plus(conf['database']['port']))
    # uri += '/{}'.format(quote_plus(conf['database']['name']))
    client = AsyncIOMotorClient(uri)
    app['db'] = client.get_database('ticket')
    config_database(app, uri)


def config_database(app, uri):
    client = MongoClient(uri)
    db = client.get_database('ticket')
    # db.captcha.create_index('expire_time', expireAfterSeconds=3600)
    # noinspection PyBroadException
    try:
        db.captcha.drop_index('expire_time_1')
    except Exception:
        pass
    db.captcha.create_index('expire_time', expireAfterSeconds=600)

    client.close()
    pass
