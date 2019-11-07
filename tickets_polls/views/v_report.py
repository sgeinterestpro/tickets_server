#!/usr/bin/env python3
# encoding: utf-8

"""
@Time    : 2019/7/18 17:58
@Author  : Sam
@Email   : muumlover@live.com
@Blog    : https://blog.muumlover.com
@Project : tickets_server
@FileName: v_report.py
@Software: PyCharm
@license : (C) Copyright 2019 by muumlover. All rights reserved.
@Desc    : 

"""
import smtplib
from datetime import datetime

from aiohttp import web
from aiohttp.abc import Request, StreamResponse

from base import ReportBase
from middleware import auth_need, Auth
from model import User, UserInit


class ReportHandles:
    @staticmethod
    @auth_need(Auth.admin)
    async def report_export(request: Request) -> StreamResponse:

        data = await request.json()

        if 'start' not in data or 'end' not in data:
            return web.json_response({'code': -2, 'message': '请求参数错误'})

        report_type = data['type']
        date_start, date_end = data['start'], data['end']

        # 修复不选择日期直接导出报表的BUG
        try:
            datetime.strptime(date_start, "%Y-%m-%d")
            datetime.strptime(date_end, "%Y-%m-%d")
        except ValueError:
            return web.json_response({'code': -1, 'message': '请选择正确的日期'})

        reports = request.app['report']
        if report_type not in reports:
            return web.json_response({'code': -2, 'message': '报表类型错误'})

        user = await User.find_one({'wx_open_id': request['open-id']})
        user_init = await UserInit.find_one_by_user(user)

        report_class = reports[report_type]
        report = report_class(date_start, date_end)  # type: ReportBase
        # noinspection PyBroadException
        try:
            await report.send(user_init['email'])
        except smtplib.SMTPDataError as err:
            return web.json_response({'code': -3, 'message': err.smtp_error.decode()})
        except:
            return web.json_response({'code': 0, 'message': f'报表导出失败'})
        return web.json_response({'code': 0, 'message': f'报表发送到{user_init["email"]}成功'})
