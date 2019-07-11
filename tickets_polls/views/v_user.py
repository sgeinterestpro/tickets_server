#!/usr/bin/env python3
# encoding: utf-8

"""
@Time    : 2019/7/11 16:52
@Author  : Sam
@Email   : muumlover@live.com
@Blog    : https://blog.muumlover.com
@Project : tickets_server
@FileName: v_user.py
@Software: PyCharm
@license : (C) Copyright 2019 by muumlover. All rights reserved.
@Desc    : 

"""
import uuid
from datetime import datetime

from aiohttp import web

from model import User
from u_email import EmailSender


class UserHandles:

    @staticmethod
    async def user_info(request):
        db = request.app['db']
        if request.method == 'POST':
            data = await request.json()
            _ = await db.user.update_one({
                'wx_open_id': request['open-id']
            }, {
                '$set': data['userInfo']
            })
            return web.json_response({'code': 0, 'message': '用户信息更新成功'})
        elif request.method == 'GET':
            user = await User.find_or_insert_one(db, {'wx_open_id': request['open-id']})
            return web.json_response({'code': 0, 'message': '获取用户信息成功', 'data': user.to_json()})

    @staticmethod
    async def user_bind(request):
        db = request.app['db']
        user = await User.find_or_insert_one(db, {'wx_open_id': request['open-id']})
        data = await request.json()

        # todo 1.验证邮件有效性
        # todo 检查是否存在于用户基础信息表
        # todo 检查邮箱和小程序是否已经被绑定

        random_code = uuid.uuid1().hex
        url = request.app.router['email-check'].url_for(uuid=random_code)
        final_url = f'{request.url.parent}{url}'

        _ = await db.captcha.insert_one({
            'captcha': random_code,
            'email': data['email'],
            'user_id': user.object_id,
            'url': final_url,
            'expire_time': datetime.utcnow()
        })
        # noinspection PyBroadException
        try:
            EmailSender.send(
                data['email'], '票券小程序账号绑定验证邮件',
                f'您好：请<a href="{final_url}" target="_blank">点击这里</a>验证邮箱来绑定票券小程序'
            )
            return web.json_response({'code': 0, 'message': '邮件发送成功'})
        except Exception:
            return web.json_response({'code': -1, 'message': '邮件服务器繁忙'})
