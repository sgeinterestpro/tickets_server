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

# import xlwt
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

    async def get_attachs(self):
        # 创建一个文件对象
        wb = openpyxl.Workbook()
        # 创建一个sheet对象
        sheet = wb.create_sheet('Sheet1')
        # 写入文件标题
        for index, (head, width) in enumerate([
            ('序号', 6),
            ('项目', 8),
            ('票券编号', 10),
            ('领取时间', 10),
            ('领取人员', 10),
            ('使用时间', 10),
            ('检票人员', 10)
        ]):
            sheet.column_dimensions[get_column_letter(index + 1)].width = width
            cell = sheet.cell(2, index, head)
            cell.alignment = self.align
            cell.border = self.border

        sheet.cell(0, 4, self._email_subject).alignment = self.align
        # sheet.cell(1, 4, '2019年07月').alignment = self.align
        # cursor = self.db.ticket_log.find({"time": {"$gte": datetime(2016, 9, 26), "$lt": datetime(2016, 9, 27)}})
        cursor = self.db.ticket.find()
        index = 3
        async for ticket_log_doc in cursor:
            cell = sheet.cell(index, 4, ticket_log_doc['_id'])
            cell.alignment = self.align
            cell.border = self.border
            index += 1
        # 写出到IO
        output = BytesIO()
        wb.save(output)

        return f'{self._email_subject}.xls', output


if __name__ == '__main__':
    from sys import stdout

    logging.basicConfig(
        format='%(levelname)s: %(asctime)s [%(filename)s:%(lineno)d] %(message)s',
        level=logging.NOTSET,
        stream=stdout)

    from u_email import EmailSender

    ReportBase.sender = EmailSender
    # with open('test.xls', 'wb') as xls:
    #     xls.write(ReportA()._attachs[1].getvalue())
