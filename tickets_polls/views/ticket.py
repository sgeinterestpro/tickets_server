"""
filename: ticket.py
datetime: 2019-04-22
author: muumlover
"""

from aiohttp import web
from bson import ObjectId

from model import Ticket, User
from unit import get_this_week_start, get_this_week_end


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

    async def used(self, request):
        """
        使用 ticket
        :param request:
        :return:
        """
        # Todo
        return web.Response(text='Hello, world')

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
            'user': user.object_id,
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
        user = await User.find_or_insert_one(db, {'open-id': request['open-id']})
        # 获取用户信息
        this_week_start = get_this_week_start().strftime('%Y-%m-%d')
        this_week_end = get_this_week_end().strftime('%Y-%m-%d')
        count = await db.ticket.count_documents({
            'user': user.object_id,
            'date': {'$gte': this_week_start, '$lte': this_week_end}
        })

        # 领取权限检查
        if count >= 3:
            return web.json_response({'code': -1, 'message': '已超过本周领取限额'})
        data = await request.json()
        if 'date' not in data:
            # todo 返回参数错误
            pass
        else:
            # todo 检查票券日期是否在本周（服务器二次校验）
            pass

        # 生成票券
        ticket = Ticket(**data)
        ticket.user = user
        res = await db.ticket.insert_one(ticket.mongo_json())
        if res.inserted_id is None:
            return web.json_response({'code': -2, 'message': '生成票券失败'})
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
        this_week_start = get_this_week_start().strftime('%Y-%m-%d')
        this_week_end = get_this_week_end().strftime('%Y-%m-%d')
        cursor = db.ticket.find({
            'user': user.object_id,
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
