"""
filename: v_default.py
datetime: 2019-04-19
author: muumlover
"""

from aiohttp import web

from aiohttp.abc import Request, StreamResponse


async def default_handle(request: Request) -> StreamResponse:
    text = "Guys, You should not access this page."
    return web.Response(text=text)
