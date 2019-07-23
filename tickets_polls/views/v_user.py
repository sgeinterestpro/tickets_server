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
from bson import ObjectId

from model import User, UserInit, Email
from u_email import EmailSender


def msg(url):
    return f'''
<p><b>尊敬的用户，您好！</b></p>
<p>感谢您使用本程序,请点击以下链接绑定帐号:</p>
<p><a href="{url}" target="_blank">立即绑定帐号</a></p>
<br/>
<p>如果以上链接无法打开，请把下面的链接复制到浏览器地址栏中打开：{url}</p>
'''


class UserHandles:

    @staticmethod
    async def user_info(request):
        db = request.app['db']
        user_info = {}
        user = await User.find_one(db, {'wx_open_id': request['open-id']})
        user_init = await UserInit.find_one(db, {'_id': user['init_id']})
        if user_init is not None:
            user_info.update(user_init.to_json())
        user_info.update(user.to_json())
        return web.json_response({'code': 0, 'message': '获取用户信息成功', 'data': user_info})

    @staticmethod
    async def user_update(request):
        db = request.app['db']
        data = await request.json()
        if 'userInfo' not in data:
            return web.json_response({'code': -2, 'message': '用户信息不存在'})
        user = await User.find_or_insert_one(db, {'wx_open_id': request['open-id']})
        _ = await db.user.update_one(user.to_object(), {
            '$set': data['userInfo']
        })
        return web.json_response({'code': 0, 'message': '同步用户信息成功'})

    @staticmethod
    async def user_bind(request):
        db = request.app['db']
        user = await User.find_one(db, {'wx_open_id': request['open-id']})
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
            'user_id': user.mongo_id,
            'url': final_url,
            'expire_time': datetime.utcnow()
        })

        email_server = await Email.use_one(db)
        # noinspection PyBroadException
        try:
            EmailSender.send(
                email_server,
                data['email'], '票券小程序账号绑定验证邮件',
                msg(final_url)
            )

            return web.json_response({'code': 0, 'message': '邮件发送成功'})
        except Exception:
            return web.json_response({'code': -3, 'message': '邮件服务器繁忙'})

    @staticmethod
    async def member_add(request):
        db = request.app['db']
        data = await request.json()

        if 'real_name' not in data or not data['real_name']:
            return web.json_response({'code': -2, 'message': '姓名不能为空'})
        if 'work_no' not in data or not data['work_no']:
            return web.json_response({'code': -2, 'message': '工号不能为空'})
        if 'email' not in data or not data['email']:
            return web.json_response({'code': -2, 'message': '电子邮件不能为空'})
        if 'phone' not in data or not data['phone']:
            return web.json_response({'code': -2, 'message': '手机号码不能为空'})
        if 'sports' not in data or not data['sports']:
            return web.json_response({'code': -2, 'message': '运动项目不能为空'})
        if 'role' not in data or not data['role']:
            return web.json_response({'code': -2, 'message': '用户角色不能为空'})

        res = await db.user_init.insert_one(data)
        if res.inserted_id is None:
            return web.json_response({'code': -3, 'message': '保存用户数据失败'})

        return web.json_response({'code': 0, 'message': '添加用户成功'})

    @staticmethod
    async def member_delete(request):
        db = request.app['db']
        data = await request.json()
        if 'init_id' not in data:
            return web.json_response({'code': -1, 'message': '请求参数错误'})

        user = await User.find_one(db, {'wx_open_id': request['open-id']})
        if data['init_id'] == str(user['init_id']):
            return web.json_response({'code': -1, 'message': '无法删除正在使用的账号'})

        res = await db.user_init.delete_one({'_id': ObjectId(data['init_id'])})
        if res.deleted_count == 0:
            return web.json_response({'code': -3, 'message': '删除用户数据失败'})

        return web.json_response({'code': 0, 'message': '删除用户成功'})

    @staticmethod
    async def member_find(request):
        db = request.app['db']
        data = await request.json()
        if 'init_id' not in data:
            return web.json_response({'code': -1, 'message': '请求参数错误'})

        user = await User.find_one(db, {'wx_open_id': request['open-id']})
        user_init = await UserInit.find_one(db, {'_id': user['init_id']})

        if 'admin' not in user_init['role']:
            return web.json_response({'code': -1, 'message': '没有相应权限'})

        user_info = {}

        t_user_init = await UserInit.find_one(db, {'_id': ObjectId(data['init_id'])})

        t_user = await User.find_one(db, {'init_id': t_user_init.mongo_id})
        if t_user is not None:
            user_info.update(t_user.to_json())
            user_info['user_id'] = user_info.pop('_id')

        user_info.update(t_user_init.to_json())
        user_info['init_id'] = user_info.pop('_id')

        return web.json_response({'code': 0, 'message': '获取用户信息成功', 'data': user_info})

    @staticmethod
    async def member_list(request):
        db = request.app['db']
        cursor = db.user_init.find()

        count, items = 0, []
        # for ticket in await cursor.to_list(length=100):
        async for user_init_doc in cursor:
            user_info = {}

            t_user_init = UserInit(**user_init_doc)

            t_user = await User.find_one(db, {'init_id': t_user_init.mongo_id})
            if t_user is not None:
                user_info.update(t_user.to_json())
                user_info['user_id'] = user_info.pop('_id')

            user_info.update(t_user_init.to_json())
            user_info['init_id'] = user_info.pop('_id')

            items.append(user_info)
            count += 1

        return web.json_response({'code': 0, 'message': '获取用户列表成功', 'count': count, 'items': items})
