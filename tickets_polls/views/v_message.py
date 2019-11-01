#!/usr/bin/env python3
# encoding: utf-8

"""
@Time    : 2019/9/25 13:43 
@Author  : Sam
@Email   : muumlover@live.com
@Blog    : https://blog.muumlover.com
@Project : tickets_server
@FileName: v_message
@Software: PyCharm
@license : (C) Copyright 2019 by muumlover. All rights reserved.
@Desc    : 
    
"""
import pymongo
from aiohttp import web
from aiohttp.abc import Request, StreamResponse

from middleware import Auth, auth_need
from model import User, Message, Ticket


class MessageHandles:
    @staticmethod
    @auth_need(Auth.role)
    async def message_count(request: Request) -> StreamResponse:
        if request['user_init'].role_check('admin'):
            message_types = [Message.State.admin_check, Message.State.notice]
        else:
            message_types = [Message.State.notice]

        count = await Message.count({
            'state': 'valid',
            'type': {'$in': message_types},
            # 'operator': {'$ne': user.mongo_id}
        })

        return web.json_response({'code': 0, 'message': '获取成功', 'count': count})

    @staticmethod
    @auth_need(Auth.role)
    async def message_list(request: Request) -> StreamResponse:
        if request['user_init'].role_check('admin'):
            message_types = [Message.State.admin_check, Message.State.notice]
        else:
            message_types = [Message.State.notice]

        cursor = Message.find({
            # 'state': 'valid',
            'type': {'$in': message_types},
            # 'operator': {'$ne': user.mongo_id}
        }).sort([('time', pymongo.DESCENDING)])

        message_list = []
        async for message in cursor:
            message_list.append(message.to_json())

        return web.json_response({'code': 0, 'message': '获取成功', 'count': len(message_list), 'items': message_list})

    @staticmethod
    @auth_need(Auth.role)
    async def message_action(request: Request) -> StreamResponse:
        data = await request.json()
        if 'message_id' not in data or not data['message_id']:
            return web.json_response({'code': -2, 'message': '请求参数错误'})

        message = await Message.find_one({'_id': data['message_id'], 'state': 'valid'})
        if message is None:
            return web.json_response({'code': -1, 'message': '无效的消息'})

        operator = await User.find_one({'_id': message['operator']})
        if operator is None:
            _ = await Message.update_one({'_id': message.mongo_id}, {'$set': {
                'checker': request['user'].mongo_id,
                'state': 'fail'
            }})
            return web.json_response({'code': -1, 'message': '操作发起者已注销', 'data': data})

        if request['user'] == operator:
            return web.json_response({'code': -1, 'message': '不能由操作发起者执行复核操作', 'data': data})

        if message['operation'] == 'ticket_generate':
            # 执行增发操作
            raise_count = message['params'].get('count', 0)
            inserted_ids = await Ticket.generate(operator, raise_count)  # 新加的
            if len(inserted_ids) == 0:
                return web.json_response({'code': -3, 'message': '票券增发成功'})
            # 更新消息状态
            _ = await Message.update_one({'_id': message.mongo_id}, {'$set': {
                'checker': request['user'].mongo_id,
                'state': 'success'
            }})

            return web.json_response({'code': 0, 'message': '票券增发成功', 'data': data})
        return web.json_response({'code': -1, 'message': '操作执行失败'})
