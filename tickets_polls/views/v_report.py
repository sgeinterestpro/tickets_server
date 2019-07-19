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
from aiohttp import web

from model import User, UserInit


class ReportHandles:
    @staticmethod
    async def report_export(request):
        db = request.app['db']
        data = await request.json()

        if 'start' not in data or 'end' not in data:
            return web.json_response({'code': -2, 'message': '请求参数错误'})

        report_type = data['type']
        date_start, date_end = data['start'], data['end']

        reports = request.app['report']
        if report_type not in reports:
            return web.json_response({'code': -2, 'message': '报表类型错误'})

        user = await User.find_one(db, {'wx_open_id': request['open-id']})
        user_init = await UserInit.find_one(db, {'_id': user['init_id']})

        report_class = reports[report_type]
        report = report_class(date_start, date_end)
        await report.send(user_init['email'])

        return web.json_response({'code': 0, 'message': f'报表发送到{user_init["email"]}成功'})
