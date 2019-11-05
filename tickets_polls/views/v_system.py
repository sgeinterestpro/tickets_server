#!/usr/bin/env python3
# encoding: utf-8

"""
@Time    : 2019/8/13 21:34 
@Author  : Sam
@Email   : muumlover@live.com
@Blog    : https://blog.muumlover.com
@Project : tickets_server
@FileName: v_system
@Software: PyCharm
@license : (C) Copyright 2019 by muumlover. All rights reserved.
@Desc    : 
    
"""
import aiohttp
from aiohttp import web
from aiohttp.abc import Request, StreamResponse
from cryptography.hazmat.primitives import serialization


class SystemHandles:
    @staticmethod
    async def rsa_pub_key(request: Request) -> StreamResponse:
        private_key = request.app['private_key']
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return web.Response(text=public_pem.decode())

    @staticmethod
    async def user_config(request: Request) -> StreamResponse:
        return web.Response(text='')

    @staticmethod
    async def system_config(request: Request) -> StreamResponse:
        return web.Response(text='')


class WeiXinHandles:
    @staticmethod
    async def login(request: Request) -> StreamResponse:
        data = await request.json()
        weixin_config = request.app['config'].get('weixin', {})
        params = [
            ('appid', weixin_config.get('appid', '')),
            ('secret', weixin_config.get('secret', '')),
            ('js_code', data.get('js_code', '')),
            ('grant_type', 'authorization_code'),
        ]
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.weixin.qq.com/sns/jscode2session', params=params) as resp:
                text = await resp.text()
        return web.Response(status=resp.status, reason=resp.reason, text=text)
