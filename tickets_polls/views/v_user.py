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
            user_info = {}
            user = await User.find_or_insert_one(db, {'wx_open_id': request['open-id']})
            user_init = await db.user_init.find_one({'_id': user['init_id']})
            if user_init is not None:
                user_init.pop('_id')
                user_info.update(user_init)
            user_info.update(user.to_json())
            return web.json_response({'code': 0, 'message': '获取用户信息成功', 'data': user_info})

    @staticmethod
    async def user_bind(request):
        db = request.app['db']
        user = await User.find_or_insert_one(db, {'wx_open_id': request['open-id']})
        data = await request.json()

        if user['init_id']:
            return web.json_response({'code': -1, 'message': '该微信已经绑定了其他邮箱'})

        user_init_doc = await db.user_init.find_one({'email': data['email']})
        if not user_init_doc:
            return web.json_response({'code': -1, 'message': '该邮箱非组织内部人员邮箱'})

        count = await db.user.count_documents({'email': data['email']})
        if count > 0:
            return web.json_response({'code': -1, 'message': '该邮箱已经绑定了其他微信'})

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
                f'''
您好：请<a href="{final_url}" target="_blank">点击这里</a>验证邮箱来绑定票券小程序
'''
            )
            return web.json_response({'code': 0, 'message': '邮件发送成功'})
        except Exception:
            return web.json_response({'code': -1, 'message': '邮件服务器繁忙'})
