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

import xlwt


def setup_report(app):
    ReportBase.sender = app['email']
    ReportBase.db = app['db']
    app['report'] = {
        'ReportBase': ReportBase,
        'ReportA': ReportA
    }


class ReportBase:
    sender = None
    db = None

    _email_subject = '报表导出'

    alignment = xlwt.Alignment()
    alignment.horz = xlwt.Alignment.HORZ_CENTER

    borders = xlwt.Borders()
    borders.left = xlwt.Borders.THIN
    borders.right = xlwt.Borders.THIN
    borders.top = xlwt.Borders.THIN
    borders.bottom = xlwt.Borders.THIN

    style_alignment = xlwt.XFStyle()
    style_alignment.alignment = alignment

    style_alignment_borders = xlwt.XFStyle()
    style_alignment_borders.alignment = alignment
    style_alignment_borders.borders = borders

    @property
    def _mail_msg(self):
        return None

    @property
    def _attachs(self):
        return None

    def send(self, email_addr):
        self.sender.send(email_addr, self._email_subject, self._mail_msg, self._attachs)


class ReportA(ReportBase):
    # _email_subject = '活动券领用存月报表'
    _email_subject = 'ReportA'

    @property
    def _mail_msg(self):
        return '您好：请在这里<a class="follow-nickName" href="https://me.csdn.net/offbeatmine" target="_blank">下载报表</a>'

    @property
    def _attachs(self):
        # 创建一个文件对象
        wb = xlwt.Workbook(encoding='utf8')
        # 创建一个sheet对象
        sheet = wb.add_sheet('Sheet1')

        # 写入文件标题
        # sheet.write(0, 0, '申请编号', self.style_heading)
        # sheet.write(0, 1, '客户名称', self.style_heading)
        # sheet.write(0, 2, '联系方式', self.style_heading)
        # sheet.write(0, 3, '身份证号码', self.style_heading)
        # sheet.write(0, 4, '办理日期', self.style_heading)
        # sheet.write(0, 5, '处理人', self.style_heading)
        # sheet.write(0, 6, '处理状态', self.style_heading)
        # sheet.write(0, 7, '处理时间', self.style_heading)
        # 写入文件标题
        for index, (head, width) in enumerate([
            ('序号', 6),
            ('项目', 8),
            ('初期增加', 10),
            ('本期增加', 10),
            ('本期领用', 10),
            ('本期作废', 10),
            ('本期使用', 10),
            ('末期库存', 10)
        ]):
            # sheet.col(index).width = width
            sheet.write(2, index, head, self.style_alignment_borders)
        sheet.write(0, 4, '活动券领用存月报表', self.style_alignment)
        sheet.write(1, 4, '2019年07月', self.style_alignment)
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
    # ReportA().send('wangsen@primeton.com')
    with open('test.xls', 'wb') as xls:
        xls.write(ReportA()._attachs[1].getvalue())
