import asyncio
import pathlib
import unittest
from datetime import datetime
from urllib.parse import quote_plus

from motor.motor_asyncio import AsyncIOMotorClient

from config import load_config
from u_email import EmailSender


def date_convert(date, fmt):
    return datetime.strptime(date, "%Y-%m-%d").strftime(fmt)


def async_test(f):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(f(*args, **kwargs))

    return wrapper


class TestBase(unittest.TestCase):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        uri = 'mongodb://'
        uri += '{}:{}'.format(quote_plus('127.0.0.1'), quote_plus('27017'))
        client = AsyncIOMotorClient(uri)
        self.db = client.get_database('ticket')
        self.sender = EmailSender
        self.config = load_config(str(pathlib.Path('..') / 'config' / 'polls.yaml'))


if __name__ == '__main__':
    unittest.main()
