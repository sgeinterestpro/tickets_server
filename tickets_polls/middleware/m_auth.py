"""
filename: m_auth.py
datetime: 2019-04-25
author: muumlover
"""
from typing import Callable, Awaitable

from aiohttp.abc import Request, StreamResponse
from aiohttp.web_exceptions import HTTPForbidden
from aiohttp.web_middlewares import middleware


@middleware
async def auth_middleware(request: Request, handler: Callable[[Request], Awaitable[StreamResponse]]) -> StreamResponse:
    if request.rel_url.parts[1] != 'web':
        if not request.headers.get('open-id'):
            return HTTPForbidden()
        request['open-id'] = request.headers.get('open-id')
    resp = await handler(request)
    return resp
