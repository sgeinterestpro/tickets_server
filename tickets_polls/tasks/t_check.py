#!/usr/bin/env python3
# encoding: utf-8

"""
@Time    : 2019/8/1 16:54
@Author  : Sam
@Email   : muumlover@live.com
@Blog    : https://blog.muumlover.com
@Project : tickets_server
@FileName: t_check.py
@Software: PyCharm
@license : (C) Copyright 2019 by muumlover. All rights reserved.
@Desc    : 

"""
import logging
from datetime import datetime, timedelta

from model import Ticket, TicketCheck


async def check(app):
    logging.info(f'开始统计票券钩稽关系')
    db = app['db']
    state_map = app['config'].get('ticket', {}).get('state', {})
    ticket_check = {
        'checked_date': (datetime.now() + timedelta(days=-1)).strftime('%Y-%m-%d'),
        'all': await Ticket.count_documents({})
    }
    for state in state_map.keys():
        count = await Ticket.count_documents({
            'state': state,
        })
        ticket_check[state] = count
    ticket_check['check_time'] = datetime.now()
    _ = await TicketCheck.insert_one(ticket_check)
    logging.info(f'票券钩稽关系统计完成')
