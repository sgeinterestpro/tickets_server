#!/usr/bin/env python3
# encoding: utf-8

"""
@Time    : 2019/8/1 16:54
@Author  : Sam
@Email   : muumlover@live.com
@Blog    : https://blog.muumlover.com
@Project : tickets_server
@FileName: t_notice.py
@Software: PyCharm
@license : (C) Copyright 2019 by muumlover. All rights reserved.
@Desc    : 

"""
import logging
import smtplib
from datetime import timedelta, datetime

from aiohttp.abc import Application

from base import ReportUsedDtl
from model import UserInit, Ticket


async def notice(app: Application) -> None:
    logging.info(f'开始推送上一日报表')
    db = app['db']
    last_date = (datetime.now() + timedelta(days=-1)).strftime('%Y-%m-%d')
    count = await Ticket.count({
        'state': 'verified',
        'expiry_date': {'$gte': last_date, '$lte': last_date}
    })
    if count == 0:
        logging.info(f'上一个自然日期{last_date}未产生数据')
        return
    report = ReportUsedDtl(last_date, None)
    cursor = UserInit.find({
        'role': 'admin'
    })
    email_list = []
    async for user_init in cursor:
        email_list.append(user_init['email'])
    try:
        await report.send(email_list)
        logging.info(f'发送通知到{email_list}成功')
    except smtplib.SMTPDataError as err:
        logging.info(f'发送通知到{email_list}失败')
        logging.exception(err)
    logging.info(f'上一日报表推送完毕')
