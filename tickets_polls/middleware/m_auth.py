"""
filename: m_auth.py
datetime: 2019-04-25
author: muumlover
"""
import json
import logging
from typing import Callable, Awaitable

import pymongo
from aiohttp import web
from aiohttp.abc import Request, StreamResponse
from aiohttp.web_exceptions import HTTPForbidden
from aiohttp.web_middlewares import middleware

from model import User, UserInit, SystemStatus


class Auth:
    weapp = 'we-app'
    user = 'user'
    admin = 'admin'
    checker = 'checker'
    system = 'system'
    role = [user, admin, checker, system]


@middleware
async def auth_middleware(request: Request, handler: Callable[[Request], Awaitable[StreamResponse]]) -> StreamResponse:
    request['open-id'] = request.headers.get('open-id', '')
    resp = await handler(request)
    return resp


def auth_need(role=None):
    def auth_decorator(func: Callable[[Request], Awaitable[StreamResponse]]):
        async def wrapped_function(request: Request) -> StreamResponse:
            try:
                async for sys_status in SystemStatus.find({}).sort([('_id', pymongo.DESCENDING)]).limit(1):
                    if sys_status['status'] != 0:
                        msg = sys_status['message'] or '系统已停止服务，具体原因请联系管理员'
                        return HTTPForbidden(reason=msg)
                    break

                if role is None:
                    return await func(request)

                if not request['open-id']:
                    return HTTPForbidden(reason='此接口仅支持通过小程序访问')

                request['user'] = await User.find_one({'wx_open_id': request['open-id']})
                if not request['user']:
                    return HTTPForbidden(reason='此接口仅支持小程序用户访问')
                if role == Auth.weapp:
                    return await func(request)

                request['user_init'] = await UserInit.find_one_by_user(request['user'])
                if not request['user_init']:
                    return HTTPForbidden(reason='此接口仅支持已认证用户访问')
                if request['user_init'].get('state') == 'suspend':
                    return HTTPForbidden(reason='此账户已被管理员停用')
                if role == Auth.role:
                    return await func(request)

                if role not in Auth.role:
                    return HTTPForbidden(reason=f'权限代码{role}是错误的')
                if request['user_init'].role_check(role):
                    return await func(request)
                else:
                    return web.json_response({'code': -1, 'message': '您没有相应操作的权限'})
            except json.JSONDecodeError as e:
                logging.error(f'错误的请求数据: \n{await request.text()}')
                return web.json_response({'code': -1, 'message': '请求数据错误'})
            except Exception as e:
                logging.error(f'请求数据: \n{await request.text()}')
                logging.exception(e)
                return web.json_response({'code': -1, 'message': '未知错误'})

        return wrapped_function

    return auth_decorator
