"""
filename: t_expiry.py
datetime: 2019-05-29
author: muumlover
"""
import logging
from datetime import datetime

from aiohttp.abc import Application

from model import Ticket


async def expiry(app: Application) -> None:
    logging.info(f'开始处理过期票券')
    db = app['db']
    date_now = datetime.now().strftime('%Y-%m-%d')
    res = await Ticket.update_many({
        'state': 'valid',
        'expiry_date': {'$lt': date_now}
    }, {
        '$set': {
            'state': 'expired',
            'overdue_time': datetime.now()
        }
    })
    logging.info(f'本次处理过期票券{res.modified_count}张')
