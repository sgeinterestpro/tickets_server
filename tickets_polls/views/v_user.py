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
from aiohttp.abc import Request, StreamResponse
from bson import ObjectId

from base import EmailSender
from middleware import Auth, auth_need
from model import User, UserInit, Captcha, OperateLog
from unit import get_sport


def msg(url):
    return f'''<p> 您好！感谢您使用本程序,请点击以下链接绑定帐号: </p>
<p> <a href="{url}" target="_blank"> 立即绑定帐号 </a> </p>
<p> 如果以上按钮无法打开，请把下面的链接复制到浏览器地址栏中打开： </p>
<p> {url} </p>
'''


class UserHandles:

    @staticmethod
    async def user_info(request: Request) -> StreamResponse:
        user_info = {}
        user = await User.find_or_insert_one({'wx_open_id': request['open-id']})
        user_init = await UserInit.find_one_by_user(user)
        if user_init is not None:
            user_info.update(user_init.to_json())
        user_info.update(user.to_json())
        user_info['sports'] = get_sport()
        # 设置默认用户的角色
        if 'role' in user_info:
            user_info['role'] = ['user'] if not user_info['role'] else user_info['role']
        if user_info.get('state') == 'suspend':
            user_info['real_name'] += ' (已停用)'
        return web.json_response({'code': 0, 'message': '获取用户信息成功', 'data': user_info})

    @staticmethod
    async def user_update(request: Request) -> StreamResponse:
        data = await request.json()
        if 'userInfo' not in data:
            return web.json_response({'code': -2, 'message': '用户信息不存在'})

        user = await User.find_or_insert_one({'wx_open_id': request['open-id']})
        _ = await User.update_one(user.to_object(), {
            '$set': data['userInfo']
        })
        return web.json_response({'code': 0, 'message': '同步用户信息成功'})

    @staticmethod
    @auth_need(Auth.weapp)
    async def user_bind(request: Request) -> StreamResponse:
        data = await request.json()

        if request['user']['init_id']:
            return web.json_response({'code': -1, 'message': '该微信已经绑定了其他邮箱'})

        user_init = await UserInit.find_one({'email': data['email']})
        if not user_init:
            return web.json_response({'code': -1, 'message': '该邮箱非组织内部人员邮箱'})

        if user_init.get('state') == 'suspend':
            return web.json_response({'code': -1, 'message': '此账户已被管理员停用'})

        count = await User.count({'email': data['email']})
        if count > 0:
            return web.json_response({'code': -1, 'message': '该邮箱已经绑定了其他微信'})

        random_code = uuid.uuid1().hex
        url = request.app.router['email-check'].url_for(uuid=random_code)
        final_url = f'{request.url.parent}{url}'

        _ = await Captcha.insert_one({
            'captcha': random_code,
            'email': data['email'],
            'user_id': request['user'].mongo_id,
            'url': final_url,
            'expire_time': datetime.utcnow()
        })

        # noinspection PyBroadException
        try:
            await EmailSender.send(
                data['email'], '票券小程序账号绑定验证邮件',
                msg(final_url)
            )

            return web.json_response({'code': 0, 'message': '邮件发送成功'})
        except Exception:
            return web.json_response({'code': -3, 'message': '邮件服务器繁忙'})

    @staticmethod
    @auth_need(Auth.admin)
    async def member_add(request: Request) -> StreamResponse:

        data = await request.json()

        if 'real_name' not in data or not data['real_name']:
            return web.json_response({'code': -2, 'message': '用户姓名不能为空'})
        if 'email' not in data or not data['email']:
            return web.json_response({'code': -2, 'message': '电子邮件不能为空'})
        if 'phone' not in data or not data['phone']:
            return web.json_response({'code': -2, 'message': '手机号码不能为空'})
        # if 'sports' not in data or not data['sports']:
        #     return web.json_response({'code': -2, 'message': '运动项目不能为空'})
        if 'role' not in data or not data['role']:
            return web.json_response({'code': -2, 'message': '用户角色不能为空'})

        res = await UserInit.insert_one(data)
        if res.inserted_id is None:
            return web.json_response({'code': -3, 'message': '保存用户数据失败'})

        _ = await OperateLog.insert_one(
            {'operator_id': request['user']['init_id'], 'option': 'member_add', 'param': data['init_id']})

        return web.json_response({'code': 0, 'message': '添加用户成功'})

    @staticmethod
    @auth_need(Auth.admin)
    async def member_suspend(request: Request) -> StreamResponse:
        data = await request.json()
        if 'init_id' not in data:
            return web.json_response({'code': -1, 'message': '请求参数错误'})

        if data['init_id'] == str(request['user']['init_id']):
            return web.json_response({'code': -1, 'message': '无法停用正在使用的账号'})

        res = await UserInit.update_one({'_id': ObjectId(data['init_id']), 'state': None}, {'$set': {
            'state': 'suspend'
        }})
        if res.matched_count == 0:
            return web.json_response({'code': -1, 'message': '未找到对应的用户'})
        if res.modified_count == 0:
            return web.json_response({'code': -3, 'message': '修改用户信息失败'})

        _ = await OperateLog.insert_one(
            {'operator_id': request['user']['init_id'], 'option': 'member_suspend', 'param': data['init_id']})

        return web.json_response({'code': 0, 'message': '停用用户成功'})

    @staticmethod
    @auth_need(Auth.admin)
    async def member_resume(request: Request) -> StreamResponse:
        data = await request.json()
        if 'init_id' not in data:
            return web.json_response({'code': -1, 'message': '请求参数错误'})

        if data['init_id'] == str(request['user']['init_id']):
            return web.json_response({'code': -1, 'message': '无法操作正在使用的账号'})

        res = await UserInit.update_one({'_id': ObjectId(data['init_id']), 'state': 'suspend'}, {'$set': {
            'state': None
        }})
        if res.matched_count == 0:
            return web.json_response({'code': -1, 'message': '未找到对应的用户'})
        if res.modified_count == 0:
            return web.json_response({'code': -3, 'message': '修改用户信息失败'})

        _ = await OperateLog.insert_one(
            {'operator_id': request['user']['init_id'], 'option': 'member_resume', 'param': data['init_id']})

        return web.json_response({'code': 0, 'message': '恢复用户成功'})

    @staticmethod
    @auth_need(Auth.admin)
    async def member_delete_temp(request: Request) -> StreamResponse:
        """
        临时替换删除按钮的功能
        """
        data = await request.json()
        if 'init_id' not in data:
            return web.json_response({'code': -1, 'message': '请求参数错误'})

        if data['init_id'] == str(request['user']['init_id']):
            return web.json_response({'code': -1, 'message': '无法操作正在使用的账号'})

        user_init = await UserInit.find_one({'_id': ObjectId(data['init_id'])})
        if user_init.get('state') is None:
            res = await UserInit.update_one({'_id': ObjectId(data['init_id']), 'state': None}, {'$set': {
                'state': 'suspend'
            }})
            if res.matched_count == 0:
                return web.json_response({'code': -1, 'message': '未找到对应的用户'})
            if res.modified_count == 0:
                return web.json_response({'code': -3, 'message': '修改用户信息失败'})

            _ = await OperateLog.insert_one(
                {'operator_id': request['user']['init_id'], 'option': 'member_suspend', 'param': data['init_id']})

            return web.json_response({'code': 0, 'message': '停用用户成功'})
        else:
            res = await UserInit.update_one({'_id': ObjectId(data['init_id']), 'state': 'suspend'}, {'$set': {
                'state': None
            }})
            if res.matched_count == 0:
                return web.json_response({'code': -1, 'message': '未找到对应的用户'})
            if res.modified_count == 0:
                return web.json_response({'code': -3, 'message': '修改用户信息失败'})

            _ = await OperateLog.insert_one(
                {'operator_id': request['user']['init_id'], 'option': 'member_resume', 'param': data['init_id']})

            return web.json_response({'code': 0, 'message': '恢复用户成功'})

    @staticmethod
    @auth_need(Auth.system)
    async def member_delete(request: Request) -> StreamResponse:
        data = await request.json()
        if 'init_id' not in data:
            return web.json_response({'code': -1, 'message': '请求参数错误'})

        if data['init_id'] == str(request['user']['init_id']):
            return web.json_response({'code': -1, 'message': '无法删除正在使用的账号'})

        res = await UserInit.delete_one({'_id': ObjectId(data['init_id'])})
        if res.deleted_count == 0:
            return web.json_response({'code': -3, 'message': '删除用户数据失败'})

        _ = await OperateLog.insert_one(
            {'operator_id': request['user']['init_id'], 'option': 'member_delete', 'param': data['init_id']})

        return web.json_response({'code': 0, 'message': '删除用户成功'})

    @staticmethod
    @auth_need(Auth.admin)
    async def member_find(request: Request) -> StreamResponse:
        data = await request.json()
        if 'init_id' not in data:
            return web.json_response({'code': -1, 'message': '请求参数错误'})

        user_info = {}
        user_init = await UserInit.find_one({'_id': ObjectId(data['init_id'])})
        user = await User.find_one({'init_id': user_init.mongo_id})
        if user is not None:
            user_info.update(user.to_json())
            user_info['user_id'] = user_info.pop('_id')
        user_info.update(user_init.to_json())
        user_info['init_id'] = user_info.pop('_id')
        # 设置默认用户的角色
        if 'role' in user_info:
            user_info['role'] = ['user'] if not user_info['role'] else user_info['role']
        if user_info.get('state') == 'suspend':
            user_info['real_name'] += ' (已停用)'
        return web.json_response({'code': 0, 'message': '获取用户信息成功', 'data': user_info})

    @staticmethod
    @auth_need(Auth.admin)
    async def member_list(request: Request) -> StreamResponse:
        cursor = UserInit.find()

        count, items = 0, []
        # for ticket in await cursor.to_list(length=100):
        async for user_init in cursor:
            user_info = {}

            t_user = await User.find_one({'init_id': user_init.mongo_id})
            if t_user is not None:
                user_info.update(t_user.to_json())
                user_info['user_id'] = user_info.pop('_id')

            user_info.update(user_init.to_json())
            user_info['init_id'] = user_info.pop('_id')

            if user_info.get('state') == 'suspend':
                user_info['real_name'] += ' (已停用)'

            items.append(user_info)
            count += 1

        return web.json_response({'code': 0, 'message': '获取用户列表成功', 'count': count, 'items': items})
