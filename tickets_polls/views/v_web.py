#!/usr/bin/env python3
# encoding: utf-8

"""
@Time    : 2019/7/11 19:46
@Author  : Sam
@Email   : muumlover@live.com
@Blog    : https://blog.muumlover.com
@Project : tickets_server
@FileName: v_web.py
@Software: PyCharm
@license : (C) Copyright 2019 by muumlover. All rights reserved.
@Desc    : 

"""
from aiohttp import web
from aiohttp.abc import Request, StreamResponse

from model import User, UserInit, Captcha


class WebHandles:
    @staticmethod
    async def email_check(request: Request) -> StreamResponse:
        random_code = request.match_info.get('uuid', '')
        captcha = await Captcha.find_one({
            'captcha': random_code,
        })
        if captcha is None:
            return web.Response(text='验证链接已经失效')

        user_init = await UserInit.find_one({'email': captcha['email']})

        if user_init.get('state') == 'suspend':
            return web.Response(text='此账户已被管理员停用')

        _ = await User.update_one({
            '_id': captcha['user_id']
        }, {
            '$set': {'init_id': user_init.mongo_id}
        })

        _ = await Captcha.delete_one({
            'captcha': random_code,
        })
        return web.Response(text='电子邮件绑定成功')
