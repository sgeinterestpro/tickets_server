"""
filename: ticket.py
datetime: 2019-04-22
author: muumlover
"""
from datetime import datetime

from aiohttp import web
from bson import ObjectId

from model import Ticket, User
from unit import date_week_start, date_week_end


class TicketRouter(web.View):

    async def get(self):
        ticket_id = self.request.match_info.get('ticket_id', None)
        if ticket_id is None:
            # 获取 ticket 列表
            return await TicketHandle.list(self.request)
        else:
            # 获取某个 ticket 信息
            return await TicketHandle(ticket_id).info(self.request)

    async def post(self):
        ticket_id = self.request.match_info.get('ticket_id', None)
        if ticket_id is None:
            # 创建一个新的 ticket
            return await TicketHandle.apply(self.request)
        else:
            return web.HTTPNotFound()

    async def put(self):
        ticket_id = self.request.match_info.get('ticket_id', None)
        if ticket_id is None:
            return web.HTTPNotFound()
        else:
            # 使用一个 ticket
            return await TicketHandle(ticket_id).used(self.request)

    async def delete(self):
        ticket_id = self.request.match_info.get('ticket_id', None)
        if ticket_id is None:
            return web.HTTPNotFound()
        else:
            # 删除一个 ticket
            return await TicketHandle(ticket_id).delete(self.request)


class TicketHandle:
    def __init__(self, ticket_id):
        self.ticket_id = ticket_id

    async def info(self, request):
        """
        获取 ticket 信息
        :param request:
        :return:
        """
        db = request.app['db']
        ticket_doc = await db.ticket.find_one({
            '_id': ObjectId(self.ticket_id)
        })
        if ticket_doc is None:
            return web.json_response({'code': -1, 'message': '未找到此票券'})
        ticket = Ticket(**ticket_doc)
        user_doc = await db.user.find_one({
            '_id': ticket.user_id
        })
        user = User(**user_doc)
        return web.json_response({'code': 0, 'ticket': ticket.api_json(), 'user': user.api_json()})

    async def used(self, request):
        """
        使用 ticket
        :param request:
        :return:
        """
        # Todo
        db = request.app['db']
        ticket_doc = await db.ticket.find_one({
            '_id': ObjectId(self.ticket_id),
        })
        
        if ticket_doc is None:
            return web.json_response({'code': -1, 'message': '此券不存在'})
        if ticket_doc['state'] == 'used':
            return web.json_response({'code': -1, 'message': '此券已被使用'})
        if ticket_doc['state'] == 'expired':
            return web.json_response({'code': -1, 'message': '此券已过期'})
        if ticket_doc['state'] != 'unused':
            return web.json_response({'code': -1, 'message': '此券状态异常'})
        date_now = datetime.now().strftime('%Y-%m-%d')
        if ticket_doc['date'] < date_now:
            return web.json_response({'code': -1, 'message': '此券已过期'})
        if ticket_doc['date'] > date_now:
            return web.json_response({'code': -1, 'message': '此券未生效'})

        user = await User.find_or_insert_one(db, {'open-id': request['open-id']})
        res = await db.ticket.update_one({
            '_id': ObjectId(self.ticket_id)
        }, {
            '$set': {'state': 'used', 'user': user.object_id}
        })

        if res.matched_count == 0:
            return web.json_response({'code': -2, 'message': '此券不存在'})
        if res.modified_count == 0:
            return web.json_response({'code': -2, 'message': '此券已被使用'})
        return web.json_response({'code': 0, 'message': '状态更新成功'})

    async def delete(self, request):
        """
        删除 ticket
        :param request:
        :return:
        """
        # todo 判断票券状态是否为已使用或已过期
        db = request.app['db']
        user = await User.find_or_insert_one(db, {'open-id': request['open-id']})
        res = await db.ticket.delete_one({
            'user_id': user.object_id,
            '_id': ObjectId(self.ticket_id)
        })
        if res.deleted_count == 0:
            return web.json_response({'code': -1, 'message': '票券不存在'})
        return web.json_response({'code': 0, 'message': '删除成功'})

    @staticmethod
    async def apply(request):
        """
        申请一张新的票券
        :param request:
        :return:
        """
        db = request.app['db']
        # 获取用户信息
        user = await User.find_or_insert_one(db, {'open-id': request['open-id']})
        data = await request.json()
        # 检查本周领取限额
        this_week_start = date_week_start().strftime('%Y-%m-%d')
        this_week_end = date_week_end().strftime('%Y-%m-%d')
        count = await db.ticket.count_documents({
            'user_id': user.object_id,
            'date': {'$gte': this_week_start, '$lte': this_week_end}
        })
        if count >= 3:
            return web.json_response({'code': -1, 'message': '已超过本周领取限额'})
        # 检查领取日期
        if 'date' not in data:
            return web.json_response({'code': -2, 'message': '请求参数错误'})
        else:
            date_now = datetime.now().strftime('%Y-%m-%d')
            if not date_now <= data['date'] <= this_week_end:
                return web.json_response({'code': -1, 'message': '所选日期无法领取'})
        # 生成票券
        ticket = Ticket(**data)
        ticket.user_id = user.object_id
        res = await db.ticket.insert_one(ticket.mongo_json())
        if res.inserted_id is None:
            return web.json_response({'code': -3, 'message': '生成票券失败'})
        data['id'] = str(res.inserted_id)
        return web.json_response({'code': 0, 'data': data})

    @staticmethod
    async def list(request):
        """
        获取用户拥有的票券
        :param request:
        :return:
        """
        db = request.app['db']
        user = await User.find_or_insert_one(db, {'open-id': request['open-id']})
        this_week_start = date_week_start().strftime('%Y-%m-%d')
        this_week_end = date_week_end().strftime('%Y-%m-%d')
        cursor = db.ticket.find({
            'user_id': user.object_id,
            'date': {'$gte': this_week_start, '$lte': this_week_end}
        })

        data = {'count': 0, 'items': []}
        # for ticket in await cursor.to_list(length=100):
        async for ticket_doc in cursor:
            ticket = Ticket(**ticket_doc)
            data['items'].append(ticket.api_json())
            data['count'] += 1

        return web.json_response(data)

    @staticmethod
    async def history(request):
        # Todo
        return web.Response(text='Hello, world')
        # data = {
        #     'count': 0,
        #     'items': [
        #         {
        #             'id': 'sp10001',
        #             'type': 'basic',
        #             'class': 'badminton',
        #             'quota': '2h',
        #             'name': '羽毛球两小时券',
        #             'receive_time': '20190101',
        #             'expiry_time': '20190108',
        #         },
        #         {
        #             'id': 'sp10002',
        #             'type': 'basic',
        #             'class': 'swim',
        #             'quota': '2h',
        #             'name': '游泳两小时券',
        #             'receive_time': '20190101',
        #             'expiry_time': '20190108',
        #         }
        #     ],
        # }
        # return web.json_response(data)
        # # return web.HTTPFound('/')
