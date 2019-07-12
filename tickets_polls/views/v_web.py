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


class WebHandles:
    @staticmethod
    async def email_check(request):
        db = request.app['db']
        random_code = request.match_info.get('uuid', '')
        captcha_doc = await db.captcha.find_one({
            'captcha': random_code,
        })
        if captcha_doc is None:
            return web.Response(text='验证链接已经失效')

        user_init_doc = await db.user_init.find_one({'email': captcha_doc['email']})
        _ = await db.user.update_one({
            '_id': captcha_doc['user_id']
        }, {
            '$set': {'init_id': user_init_doc['_id']}
        })

        _ = await db.captcha.delete_one({
            'captcha': random_code,
        })
        return web.Response(text='电子邮件绑定成功')
