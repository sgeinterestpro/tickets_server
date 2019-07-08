"""
filename: u_database.py
datetime: 2019-04-22
author: muumlover
"""

from urllib.parse import quote_plus

from motor.motor_asyncio import AsyncIOMotorClient


def setup_database(app):
    conf = app['config']
    uri = 'mongodb://'
    if conf['database']['user'] != '':
        uri += '{}:{}@'.format(quote_plus(conf['database']['user']), quote_plus(conf['database']['pass']))
    uri += '{}:{}'.format(quote_plus(conf['database']['host']), quote_plus(conf['database']['port']))
    # uri += '/{}'.format(quote_plus(conf['database']['name']))
    client = AsyncIOMotorClient(uri)
    app['db'] = client.get_database('ticket')
