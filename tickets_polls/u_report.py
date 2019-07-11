#!/usr/bin/env python3
# encoding: utf-8

"""
@Time    : 2019/7/9 12:20
@Author  : Sam
@Email   : muumlover@live.com
@Blog    : https://blog.muumlover.com
@Project : tickets_server
@FileName: u_report.py
@Software: PyCharm
@license : (C) Copyright 2019 by muumlover. All rights reserved.
@Desc    :

"""
import logging
from io import BytesIO

import openpyxl
from openpyxl.styles import Border, Side, Alignment
from openpyxl.utils import get_column_letter


def setup_report(app):
    ReportBase.sender = app['email']
    ReportBase.db = app['db']
    app['report'] = {
        'ReportBase': ReportBase,
        'ReportCheckLogFlow': ReportCheckLogFlow
    }


class ReportBase:
    sender = None
    db = None

    _email_subject = '报表导出'

    border = Border(left=Side(border_style='thin', color='000000'),
                    right=Side(border_style='thin', color='000000'),
                    top=Side(border_style='thin', color='000000'),
                    bottom=Side(border_style='thin', color='000000'))
    align = Alignment(horizontal='center', vertical='center', wrap_text=True)

    @property
    def _mail_msg(self):
        return None

    async def get_attachs(self):
        return None

    async def send(self, email_addr):
        attachs = await self.get_attachs()
        self.sender.send(email_addr, self._email_subject, self._mail_msg, attachs)


class ReportCheckLogFlow(ReportBase):
    _email_subject = '活动券使用记录流水表'

    @property
    def _mail_msg(self):
        return '您好：请在这里<a class="follow-nickName" href="https://me.csdn.net/offbeatmine" target="_blank">下载报表</a>'

    def style_body(self, cell):
        cell.alignment = self.align
        cell.border = self.border

    def style_title(self, cell):
        cell.alignment = self.align

    async def get_attachs(self):
        # 创建一个文件对象
        wb = openpyxl.Workbook()
        # 创建一个sheet对象
        sheet = wb.active
        # 写入文件标题
        for index, (head, width) in enumerate([
            ('序号', 4.63),
            ('项目', 8),
            ('票券编号', 23.25),
            ('领取时间', 21),
            ('领取人员', 10),
            ('使用时间', 21),
            ('检票人员', 10)
        ]):
            sheet.column_dimensions[get_column_letter(index + 1)].width = width
            self.style_body(sheet.cell(3, index + 1, head))

        self.style_title(sheet.cell(1, 4, self._email_subject))
        # sheet.cell(2, 5, '2019年07月').alignment = self.align
        # cursor = self.db.ticket_log.find({"time": {"$gte": datetime(2016, 9, 26), "$lt": datetime(2016, 9, 27)}})
        cursor = self.db.ticket_log.find({})
        index = 0
        async for ticket_log in cursor:
            if 'checked' != ticket_log['option']:
                continue
            ticket_doc = await self.db.ticket.find_one({
                '_id': ticket_log['ticket_id'],
            })
            purchaser = await self.db.user.find_one({
                '_id': ticket_doc['purchaser'],
            })
            checker = await self.db.user.find_one({
                '_id': ticket_doc['checker'],
            })
            self.style_body(sheet.cell(index + 4, 1, index + 1))  # 序号
            self.style_body(sheet.cell(index + 4, 2, ticket_doc['class']))  # 项目
            self.style_body(sheet.cell(index + 4, 3, ticket_doc['_id']))  # 票券编号
            self.style_body(sheet.cell(index + 4, 4, ticket_doc['purch_time']))  # 领取时间
            self.style_body(sheet.cell(index + 4, 5, purchaser['wx_open_id']))  # 领取人员
            self.style_body(sheet.cell(index + 4, 6, ticket_doc['check_time']))  # 使用时间
            self.style_body(sheet.cell(index + 4, 7, checker['wx_open_id']))  # 检票人员
            index += 1

        # 写出到IO
        output = BytesIO()
        wb.save(output)

        return f'{self._email_subject}.xlsx', output


if __name__ == '__main__':
    from sys import stdout

    logging.basicConfig(
        format='%(levelname)s: %(asctime)s [%(filename)s:%(lineno)d] %(message)s',
        level=logging.NOTSET,
        stream=stdout)

    from urllib.parse import quote_plus
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    from u_email import EmailSender

    uri = 'mongodb://'
    uri += '{}:{}'.format(quote_plus('127.0.0.1'), quote_plus('27017'))
    client = AsyncIOMotorClient(uri)

    ReportBase.db = client.get_database('ticket')
    ReportBase.sender = EmailSender


    async def test():
        with open('活动券使用记录流水表.xlsx', 'wb') as xls:
            attachs = await ReportCheckLogFlow().get_attachs()
            xls.write(attachs[1].getvalue())


    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
