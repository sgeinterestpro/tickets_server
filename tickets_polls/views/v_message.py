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

from model import User, Message, Ticket, UserInit


class MessageHandles:
    @staticmethod
    async def message_count(request):

        user = await User.m_find_one({'wx_open_id': request['open-id']})
        user_init = await UserInit.m_find_one_by_user(user)

        if user_init.is_admin:
            message_types = [Message.State.admin_check, Message.State.notice]
        else:
            message_types = [Message.State.notice]

        count = await Message.count_documents({
            'state': 'valid',
            'type': {'$in': message_types},
            # 'operator': {'$ne': user.mongo_id}
        })

        return web.json_response({'code': 0, 'message': '获取成功', 'count': count})

    @staticmethod
    async def message_list(request):
        user = await User.m_find_one({'wx_open_id': request['open-id']})
        user_init = await UserInit.m_find_one_by_user(user)

        if user_init.is_admin:
            message_types = [Message.State.admin_check, Message.State.notice]
        else:
            message_types = [Message.State.notice]

        cursor = Message.find({
            # 'state': 'valid',
            'type': {'$in': message_types},
            # 'operator': {'$ne': user.mongo_id}
        }, sort=[('time', pymongo.DESCENDING)])

        message_list = []
        async for message_doc in cursor:
            message = Message(**message_doc)
            message_list.append(message.to_json())

        return web.json_response({'code': 0, 'message': '获取成功', 'count': len(message_list), 'items': message_list})

    @staticmethod
    async def message_action(request):

        data = await request.json()
        if 'message_id' not in data or not data['message_id']:
            return web.json_response({'code': -2, 'message': '请求参数错误'})

        user = await User.m_find_one({'wx_open_id': request['open-id']})
        message = await Message.m_find_one({'_id': data['message_id'], 'state': 'valid'})

        if message is None:
            return web.json_response({'code': -1, 'message': '无效的消息'})

        if message['operation'] == 'ticket_generate':
            raiser_id = message['operator']
            raise_count = message['params'].get('count', 0)
            raiser = await User.m_find_one({'_id': raiser_id})

            inserted_ids = await Ticket.generate(raiser, raise_count)  # 新加的

            if len(inserted_ids) == 0:
                return web.json_response({'code': -3, 'message': '票券增发成功'})

            _ = await Message.update_one({'_id': message.mongo_id}, {'$set': {
                'checker': user.mongo_id,
                'state': 'success'
            }})
            return web.json_response({'code': 0, 'message': '票券增发成功', 'data': data})

        return web.json_response({'code': -1, 'message': '操作执行失败'})
