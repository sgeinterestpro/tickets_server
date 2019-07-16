"""
filename: t_expiry.py
datetime: 2019-05-29
author: muumlover
"""
import logging
from datetime import datetime


async def expiry(app):
    db = app['db']
    date_now = datetime.now().strftime('%Y-%m-%d')
    res = await db.ticket.update({
        'state': 'valid',
        'expiry_date': {'$lt': date_now}
    }, {
        '$set': {
            'state': 'expired',
            'overdue_time': datetime.now()
        }
    })
    logging.info(f'本次处理过期票券{res.modified_count}张')
