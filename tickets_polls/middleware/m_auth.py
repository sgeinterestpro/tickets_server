"""
filename: m_auth.py
datetime: 2019-04-25
author: muumlover
"""
from typing import Callable, Awaitable

from aiohttp import web
from aiohttp.abc import Request, StreamResponse
from aiohttp.web_exceptions import HTTPForbidden
from aiohttp.web_middlewares import middleware

from model import User, UserInit


class Auth:
    weapp = 'we-app'
    user = 'user'
    admin = 'admin'
    checker = 'checker'
    role = [user, admin, checker]


@middleware
async def auth_middleware(request: Request, handler: Callable[[Request], Awaitable[StreamResponse]]) -> StreamResponse:
    request['open-id'] = request.headers.get('open-id', '')
    resp = await handler(request)
    return resp


def auth_need(role=None):
    def auth_decorator(func: Callable[[Request], Awaitable[StreamResponse]]):
        async def wrapped_function(request: Request) -> StreamResponse:
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
            if role == Auth.role:
                return await func(request)

            if role not in Auth.role:
                return HTTPForbidden(reason=f'权限代码{role}是错误的')
            if request['user_init'].role_check(role):
                return await func(request)
            else:
                return web.json_response({'code': -1, 'message': '您没有相应操作的权限'})

        return wrapped_function

    return auth_decorator
