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
from aiohttp import web
from cryptography.hazmat.primitives import serialization


class SystemHandles:
    @staticmethod
    async def rsa_pub_key(request):
        private_key = request.app['private_key']
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return web.Response(text=public_pem.decode())
