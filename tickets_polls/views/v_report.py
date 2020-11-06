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
import logging
import smtplib
from json import JSONDecodeError

from aiohttp import web
from aiohttp.abc import Request, StreamResponse

from base import ReportBase
from middleware import auth_need, Auth
from model import User, UserInit


class ReportHandles:
    @staticmethod
    @auth_need(Auth.admin)
    async def report_list(request: Request) -> StreamResponse:
        reports = request.app['report']
        report_list_test = [await v.to_json(k) for k, v in reports.items()]
        return web.json_response({
            'code': 0, 'message': f'报表类型获取成功',
            'count': len(report_list_test), 'items': report_list_test
        })

    @staticmethod
    @auth_need(Auth.admin)
    async def report_export(request: Request) -> StreamResponse:
        try:
            data = await request.json()
        except JSONDecodeError:
            return web.json_response({'code': -2, 'message': '请求参数错误'})
        if 'type' not in data:
            return web.json_response({'code': -2, 'message': '请求参数错误'})

        report_type = data['type']
        reports = request.app['report']
        if report_type not in reports:
            return web.json_response({'code': -2, 'message': '报表类型错误'})

        # if 'start' in data and 'end' in data:
        #     date_start, date_end = data['start'], data['end']
        #     # 修复不选择日期直接导出报表的BUG
        #     try:
        #         datetime.strptime(date_start, "%Y-%m-%d")
        #         datetime.strptime(date_end, "%Y-%m-%d")
        #     except ValueError:
        #         return web.json_response({'code': -1, 'message': '请选择正确的日期'})

        user_init = await UserInit.find_one({'wx_open_id': request['open-id']})

        report_class = reports[report_type]
        # noinspection PyBroadException
        try:
            report = report_class(**data.get('params', {}))  # type: ReportBase
            await report.send(user_init['email'])
        except smtplib.SMTPDataError as err:
            return web.json_response({'code': -3, 'message': err.smtp_error.decode()})
        except (KeyError, TypeError) as err:
            logging.exception(err)
            return web.json_response({'code': -1, 'message': f'请填写正确的导出条件'})
        except Exception as err:
            logging.exception(err)
            return web.json_response({'code': -2, 'message': f'报表生成失败'})
        return web.json_response({'code': 0, 'message': f'报表发送到{user_init["email"]}成功'})
