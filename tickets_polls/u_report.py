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
from datetime import datetime, timedelta
from io import BytesIO

import openpyxl
from openpyxl.styles import Border, Side, Alignment, Font
from openpyxl.utils import get_column_letter

from model import Email
from u_email import EmailSender
from unit import date_month_start, date_month_end


def setup_report(app):
    ReportBase.sender = app['email']
    ReportBase.db = app['db']
    ReportBase.config = app['config']
    app['report'] = {
        'ReportBase': ReportBase,
        'ReportCheckLogFlow': ReportCheckLogFlow,
        'ReportUsedDtl': ReportUsedDtl,
        'ReportUsedDay': ReportUsedDay,
        'ReportUsedMonth': ReportUsedMonth,
        'ReportUsedSportMonth': ReportUsedSportMonth
    }


def style_title(cell):
    cell.alignment = Alignment(horizontal='center', vertical='center')
    cell.font = Font(size=16, bold=True)


def style_body(cell):
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    cell.border = Border(left=Side(border_style='thin', color='000000'),
                         right=Side(border_style='thin', color='000000'),
                         top=Side(border_style='thin', color='000000'),
                         bottom=Side(border_style='thin', color='000000'))


def date_show(date, fmt):
    return datetime.strptime(date, "%Y-%m-%d").strftime(fmt)


class ReportBase:
    sender: EmailSender = None
    db = None
    config = None
    sport_map = None
    state_map = None

    _email_subject = '报表导出'
    _email_attach = _email_subject

    def __init__(self):
        ticket_map = self.config.get('ticket', {})
        self.sport_map = ticket_map.get('sport', {})
        self.state_map = ticket_map.get('state', {})

    @property
    def _mail_msg(self):
        return f'''
<style class="fox_global_style"> 
div.fox_html_content {{ line-height: 1.5;}} 
/* 一些默认样式 */ 
blockquote {{ margin-Top: 0px; margin-Bottom: 0px; margin-Left: 0.5em }} 
ol, ul {{ margin-Top: 0px; margin-Bottom: 0px; list-style-position: inside; }} 
p {{ margin-Top: 0px; margin-Bottom: 0px }} 
</style>
<div style="border-bottom:3px solid #d9d9d9; background:url(http://exmail.qq.com/zh_CN/htmledition/images/domainmail/bizmail_bg.gif) repeat-x 0 1px #FFFFFF;"> 
    <div style="border:1px solid #c8cfda; padding:40px;"> 
        <div> 
            <p>尊敬的用户，您好！<br> <br> </p> 
            <p>您于{datetime.now().strftime("%Y-%m-%d %H:%M")}导出了《{self._email_attach}》。 <br> 附件为您本次申请导出的报表。</p> 
            <br> <br> 
        </div> 
        <div>本邮件由服务器自动发送</div> 
        <div style="border-top:1px solid #ccc;padding:10px 0;font-size:12px;margin:20px 0;"> 
            票券助手站点：<a href="http://ticket.sge-tech.com">http://ticket.sge-tech.com</a><br> 
        </div> 
    </div> 
</div>
'''

    async def get_attachs(self):
        return None

    async def send(self, email_addr):
        attachs = await self.get_attachs()
        email_server = await Email.use_one(self.db)
        self.sender.send(email_server, email_addr, self._email_subject, self._mail_msg, attachs)


class ReportCheckLogFlow(ReportBase):
    _email_subject = '活动券使用记录流水表'

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
            style_body(sheet.cell(3, index + 1, head))

        style_title(sheet.cell(1, 4, self._email_subject))
        # sheet.cell(2, 5, '2019年07月').alignment = self.align
        # cursor = self.db.ticket_log.find({"time": {"$gte": datetime(2016, 9, 26), "$lt": datetime(2016, 9, 27)}})
        cursor = self.db.ticket_log.find({})
        index = 0
        async for ticket_log in cursor:
            if 'checked' != ticket_log['option']:
                continue

            ticket_doc = await self.db.ticket.find_one({'_id': ticket_log['ticket_id'], })
            purchaser = await self.db.user.find_one({'_id': ticket_doc['purchaser'], })
            checker = await self.db.user.find_one({'_id': ticket_doc['checker'], })

            style_body(sheet.cell(index + 4, 1, index + 1))  # 序号
            style_body(sheet.cell(index + 4, 2, ticket_doc['class']))  # 项目
            style_body(sheet.cell(index + 4, 3, ticket_doc['_id']))  # 票券编号
            style_body(sheet.cell(index + 4, 4, ticket_doc['purch_time']))  # 领取时间
            style_body(sheet.cell(index + 4, 5, purchaser['realName']))  # 领取人员
            style_body(sheet.cell(index + 4, 6, ticket_doc['check_time']))  # 使用时间
            style_body(sheet.cell(index + 4, 7, checker['realName']))  # 检票人员

            index += 1

        # 写出到IO
        output = BytesIO()
        wb.save(output)

        return f'{self._email_subject}.xlsx', output


class ReportUsedDtl(ReportBase):
    _email_subject = '领用登记明细表'
    date_start = None
    date_end = None

    def __init__(self, date_start, date_end):
        super().__init__()
        self.date_start = date_start
        self.date_end = date_end
        if self.date_end > datetime.now().strftime('%Y-%m-%d'):
            self.date_end = datetime.now().strftime('%Y-%m-%d')
        self._email_attach = '{}_{}-{}'.format(
            self._email_subject,
            date_show(self.date_start, "%Y.%m.%d"),
            date_show(self.date_end, "%Y.%m.%d")
        )

    async def get_attachs(self):
        # 创建一个文件对象
        wb = openpyxl.Workbook()
        # 创建一个sheet对象
        sheet = wb.active
        # 写入报表标题
        sheet.row_dimensions[1].hight = 28.5
        sheet.merge_cells('A1:G1')
        style_title(sheet.cell(1, 1, self._email_subject))
        # 写入报表日期
        sheet.row_dimensions[2].hight = 28.5
        sheet.merge_cells('A2:G2')
        if self.date_start == self.date_end:
            date_text = self.date_start
        else:
            date_text = f'{self.date_start}至{self.date_end}'
        style_title(sheet.cell(2, 1, date_text))
        # 写入数据列标题
        for index, (head, width) in enumerate([
            ('序号', 5),
            ('部门', 10),
            ('姓名', 8.5),
            ('项目', 8.5),
            ('票券编号', 23),
            ('领取时间', 23),
            ('票券状态', 8.5)
        ]):
            sheet.column_dimensions[get_column_letter(index + 1)].width = width
            style_body(sheet.cell(3, index + 1, head))
        # 填充数据
        cursor = self.db.ticket.find({
            'expiry_date': {'$gte': self.date_start, '$lte': self.date_end}
        }).sort('expiry_date')
        date_now = self.date_end
        index = 0
        offset = 0
        async for ticket_doc in cursor:
            now_row = index + offset + 4
            if date_now != ticket_doc.get('expiry_date', '-'):
                date_now = ticket_doc.get('expiry_date', '-')
                sheet.merge_cells(start_row=now_row, start_column=1, end_row=now_row, end_column=7)
                style_body(sheet.cell(now_row, 1, date_now))  # 序号
                offset += 1
                now_row = index + offset + 4
            user = await self.db.user.find_one({'_id': ticket_doc['purchaser']})
            user_init = await self.db.user_init.find_one({'_id': (user or {}).get('init_id')})
            style_body(sheet.cell(now_row, 1, index + 1))  # 序号
            style_body(sheet.cell(now_row, 2, (user_init or {}).get('department', '-')))  # 部门
            style_body(sheet.cell(now_row, 3, (user_init or {}).get('real_name', '-')))  # 姓名
            style_body(sheet.cell(now_row, 4, self.sport_map.get(ticket_doc.get('class'), '-')))  # 项目
            style_body(sheet.cell(now_row, 5, str(ticket_doc.get('_id', '-'))[:20]))  # 票券编号
            style_body(sheet.cell(now_row, 6, ticket_doc.get('purch_time', '-')))  # 领取时间
            style_body(sheet.cell(now_row, 7, self.state_map.get(ticket_doc.get('state'), '-')))  # 票券状态
            index += 1

        # 写出到IO
        output = BytesIO()
        wb.save(output)

        return f'{self._email_attach}.xlsx', output


class ReportUsedDay(ReportBase):
    _email_subject = '领用登记日报表'
    date_start = None
    date_end = None

    def __init__(self, date_start, date_end):
        super().__init__()
        self.date_start = date_start
        self.date_end = date_end
        self._email_attach = '{}_{}-{}'.format(
            self._email_subject,
            date_show(self.date_start, "%Y.%m.%d"),
            date_show(self.date_end, "%Y.%m.%d")
        )

    async def get_attachs(self):
        # 创建一个文件对象
        wb = openpyxl.Workbook()
        # 创建一个sheet对象
        sheet = wb.active
        # 写入报表标题
        sheet.row_dimensions[1].hight = 28.5
        sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(self.sport_map) + 4)
        style_title(sheet.cell(1, 1, self._email_subject))
        # 写入数据列标题
        column = 1
        sheet.column_dimensions[get_column_letter(column)].width = 12
        style_body(sheet.cell(2, column, '日期'))
        column += 1
        for sport in self.sport_map.values():
            sheet.column_dimensions[get_column_letter(column)].width = 8.38
            style_body(sheet.cell(2, column, sport))
            column += 1
        sheet.column_dimensions[get_column_letter(column)].width = 8.38
        style_body(sheet.cell(2, column, '合计'))
        column += 1
        sheet.column_dimensions[get_column_letter(column)].width = 8.38
        style_body(sheet.cell(2, column, '作废张数'))
        column += 1
        sheet.column_dimensions[get_column_letter(column)].width = 8.38
        style_body(sheet.cell(2, column, '备注'))
        # 填充数据
        sport_days = {}
        cursor = self.db.ticket.find({
            'expiry_date': {'$gte': self.date_start, '$lte': self.date_end}
        }).sort('expiry_date')
        date_now = self.date_end
        async for ticket_doc in cursor:
            if date_now != ticket_doc.get('expiry_date', '-'):
                date_now = ticket_doc.get('expiry_date', '-')

            if date_now not in sport_days:
                sport_days[date_now] = {'expired': 0}
                sport_days[date_now].update(zip(self.sport_map.keys(), [0] * len(self.sport_map)))

            if ticket_doc.get('state') == 'verified':
                sport_days[date_now][ticket_doc.get('class')] += 1
            else:
                sport_days[date_now]['expired'] += 1

        for sport_day_i, (sport_day, sports) in enumerate(sport_days.items()):
            now_row = sport_day_i + 3
            column = 1
            style_body(sheet.cell(now_row, column, sport_day))  # 日期
            column += 1
            count_all = 0
            for sport, count in sports.items():
                if sport == 'expired':
                    continue
                style_body(sheet.cell(now_row, column, count))  # 运动项目
                count_all += count
                column += 1
            style_body(sheet.cell(now_row, column, count_all))  # 合计
            column += 1
            style_body(sheet.cell(now_row, column, sports.get('expired', 0)))  # 作废张数
            column += 1
            note = None
            if datetime.now().strftime('%Y-%m-%d') == sport_day:
                note = '今日结束后数据可能会发生变动'
            style_body(sheet.cell(now_row, column, note))  # 备注

        # 写出到IO
        output = BytesIO()
        wb.save(output)

        return f'{self._email_attach}.xlsx', output


class ReportUsedMonth(ReportBase):
    _email_subject = '领用登记月报表'
    date_start = None
    date_end = None

    def __init__(self, date_start, date_end):
        super().__init__()
        self.date_start = date_start
        self.date_end = date_end
        self._email_attach = '{}_{}-{}'.format(
            self._email_subject,
            date_show(self.date_start, "%Y.%m"),
            date_show(self.date_end, "%Y.%m")
        )

    async def get_attachs(self):
        # 创建一个文件对象
        wb = openpyxl.Workbook()
        # 创建一个sheet对象
        sheet = wb.active
        # 写入报表标题
        sheet.row_dimensions[1].hight = 28.5
        sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(self.sport_map) + 5)
        style_title(sheet.cell(1, 1, self._email_subject))
        # 写入数据列标题
        column = 1
        sheet.column_dimensions[get_column_letter(column)].width = 8.38
        style_body(sheet.cell(2, column, '年度'))
        column += 1
        sheet.column_dimensions[get_column_letter(column)].width = 8.38
        style_body(sheet.cell(2, column, '月份'))
        column += 1
        for sport in self.sport_map.values():
            sheet.column_dimensions[get_column_letter(column)].width = 8.38
            style_body(sheet.cell(2, column, sport))
            column += 1
        sheet.column_dimensions[get_column_letter(column)].width = 8.38
        style_body(sheet.cell(2, column, '合计'))
        column += 1
        sheet.column_dimensions[get_column_letter(column)].width = 8.38
        style_body(sheet.cell(2, column, '作废张数'))
        column += 1
        sheet.column_dimensions[get_column_letter(column)].width = 8.38
        style_body(sheet.cell(2, column, '备注'))
        # 填充数据
        date_start = datetime.strptime(self.date_start, '%Y-%m-%d')
        date_end = datetime.strptime(self.date_end, '%Y-%m-%d')
        month_list = []
        month_now = datetime(date_start.year, date_start.month, 15)
        month_list.append(month_now)
        while month_now < datetime(date_end.year, date_end.month, 15):
            month_now += timedelta(days=30)
            month_now += timedelta(days=15 - month_now.day)
            month_list.append(month_now)
        sport_months = {}
        for month in month_list:
            month_start = date_month_start(month)
            month_end = date_month_end(month)
            if datetime.now() < month_start:
                break

            month_start_str = month_start.strftime('%Y-%m-%d')
            month_end_str = month_end.strftime('%Y-%m-%d')
            month_str = month.strftime('%Y-%m')

            if month_str not in sport_months:
                sport_months[month_str] = {'expired': 0}
                sport_months[month_str].update(zip(self.sport_map.keys(), [0] * len(self.sport_map)))
            if datetime.now() <= month_end:
                sport_months[month_str]['un-end'] = True

            cursor = self.db.ticket.find({
                'expiry_date': {'$gte': month_start_str, '$lte': month_end_str}
            }).sort('expiry_date')
            async for ticket_doc in cursor:
                if ticket_doc.get('state') == 'verified':
                    sport_months[month_str][ticket_doc.get('class')] += 1
                else:
                    sport_months[month_str]['expired'] += 1
        for sport_month_i, (month_str, sports) in enumerate(sport_months.items()):
            year, month = month_str.split('-')
            now_row = sport_month_i + 3
            column = 1
            style_body(sheet.cell(now_row, column, year))  # 年度
            column += 1
            style_body(sheet.cell(now_row, column, month))  # 月份
            column += 1
            count_all = 0
            for sport, count in sports.items():
                if sport == 'expired' or sport == 'un-end':
                    continue
                style_body(sheet.cell(now_row, column, count))  # 运动项目
                count_all += count
                column += 1
            style_body(sheet.cell(now_row, column, count_all))  # 合计
            column += 1
            style_body(sheet.cell(now_row, column, sports.get('expired', 0)))  # 作废张数
            column += 1
            note = None
            if sports.get('un-end'):
                note = '本月结束后数据可能会发生变动'
            style_body(sheet.cell(now_row, column, note))  # 备注

        # 写出到IO
        output = BytesIO()
        wb.save(output)

        return f'{self._email_attach}.xlsx', output


class ReportUsedSportMonth(ReportBase):
    _email_subject = '活动券分项领用月报表'
    date = None

    def __init__(self, date_start, date_end):
        super().__init__()
        self.date = date_end
        self._email_attach = '{}_{}'.format(
            self._email_subject,
            date_show(self.date, "%Y.%m")
        )

    async def get_attachs(self):
        not_end = False
        month_start = date_month_start(datetime.strptime(self.date, '%Y-%m-%d'))
        month_end = date_month_end(datetime.strptime(self.date, '%Y-%m-%d'))
        if month_start < datetime.now() < month_end:
            not_end = True
        month_start = month_start.strftime('%Y-%m-%d')
        month_end = month_end.strftime('%Y-%m-%d')
        # 创建一个文件对象
        wb = openpyxl.Workbook()
        # 创建一个sheet对象
        sheet = wb.active
        # 写入报表标题
        merge_column = 5
        if not_end:
            merge_column = 6
        sheet.row_dimensions[1].hight = 28.5
        sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=merge_column)
        style_title(sheet.cell(1, 1, self._email_subject))
        # 写入报表日期
        sheet.row_dimensions[2].hight = 28.5
        sheet.merge_cells(start_row=2, start_column=1, end_row=2, end_column=merge_column)
        date_text = f'{month_start}至{month_end}'
        if not_end:
            date_text += f'【期中{datetime.now().strftime("%Y-%m-%d")}导出数据】'
        style_title(sheet.cell(2, 1, date_text))
        # 写入数据列标题
        for index, (head, width) in enumerate([
            ('序号', 8),
            ('项目', 12),
            ('本期领取', 18),
            ('本期过期作废', 18),
            ('本期实际使用', 18)
        ]):
            sheet.column_dimensions[get_column_letter(index + 1)].width = width
            style_body(sheet.cell(3, index + 1, head))
        if not_end:
            sheet.column_dimensions[get_column_letter(6)].width = 18
            style_body(sheet.cell(3, 6, '本期暂未使用'))

        # 填充数据
        sports = {}  # dict(zip(self.sport_map.keys(), [dict([('expired', 1), ('verified', 2)])] * len(self.sport_map)))
        for sport_key in self.sport_map.keys():
            sports[sport_key] = {'expired': 0, 'verified': 0, 'valid': 0}
        cursor = self.db.ticket.find({
            'expiry_date': {'$gte': month_start, '$lte': month_end}
        }).sort('expiry_date')
        async for ticket_doc in cursor:
            if ticket_doc.get('state') == 'verified':
                sports[ticket_doc.get('class')]['verified'] += 1
            elif ticket_doc.get('state') == 'expired':
                sports[ticket_doc.get('class')]['expired'] += 1
            else:
                sports[ticket_doc.get('class')]['valid'] += 1
        index = 0
        for sport, value in sports.items():
            now_row = index + 4
            style_body(sheet.cell(now_row, 1, index + 1))  # 序号
            style_body(sheet.cell(now_row, 2, self.sport_map.get(sport, '-')))  # 项目
            style_body(sheet.cell(now_row, 3, value['expired'] + value['verified']))  # 本期领取
            style_body(sheet.cell(now_row, 4, value['expired']))  # 本期过期作废
            style_body(sheet.cell(now_row, 5, value['verified']))  # 本期实际使用
            if not_end:
                style_body(sheet.cell(now_row, 6, value['valid']))  # 本期暂未使用
            index += 1

        # 写出到IO
        output = BytesIO()
        wb.save(output)

        return f'{self._email_attach}.xlsx', output


if __name__ == '__main__':
    from sys import stdout

    logging.basicConfig(
        format='%(levelname)s: %(asctime)s [%(filename)s:%(lineno)d] %(message)s',
        level=logging.NOTSET,
        stream=stdout)

    import pathlib
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    from u_email import EmailSender, EmailSender, EmailSender, EmailSender, EmailSender
    from config import load_config
    from urllib.parse import quote_plus

    uri = 'mongodb://'
    uri += '{}:{}'.format(quote_plus('127.0.0.1'), quote_plus('27017'))
    client = AsyncIOMotorClient(uri)

    ReportBase.db = client.get_database('ticket')
    ReportBase.sender = EmailSender
    ReportBase.config = load_config(str(pathlib.Path('..') / 'config' / 'polls.yaml'))


    async def test():
        with open('ReportUsedDtl.xlsx', 'wb') as xls:
            attachs = await ReportUsedDtl('2019-07-11', '2019-08-19').get_attachs()
            xls.write(attachs[1].getvalue())
        with open('ReportUsedDay.xlsx', 'wb') as xls:
            attachs = await ReportUsedDay('2019-07-11', '2019-08-19').get_attachs()
            xls.write(attachs[1].getvalue())
        with open('ReportUsedMonth.xlsx', 'wb') as xls:
            attachs = await ReportUsedMonth('2019-03-11', '2019-08-19').get_attachs()
            xls.write(attachs[1].getvalue())
        with open('ReportUsedSportMonth.xlsx', 'wb') as xls:
            attachs = await ReportUsedSportMonth('2019-07-19').get_attachs()
            xls.write(attachs[1].getvalue())


    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
