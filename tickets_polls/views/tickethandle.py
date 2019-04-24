from aiohttp import web
from bson import ObjectId

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


class Ticket:
    """
    票券对象
    """
    fled_need = ['class', 'title', 'date']

    def __init__(self, **kwargs) -> None:
        for key in self.fled_need:
            if key not in kwargs:
                kwargs[key] = None
        self._class = kwargs['class']
        self._title = kwargs['title']
        self._date = kwargs['date']

        if '_id' in kwargs:
            self._id = kwargs['_id']
            self._state = kwargs['state']
        else:
            self._id = None
            self._state = 'unused'
        pass

    @property
    def str_id(self):
        return str(self._id)

    @str_id.setter
    def str_id(self, id_):
        self._id = ObjectId(id_)

    @property
    def create_time(self):
        return self._id.generation_time.astimezone()

    def mongo_json(self):
        return {
            'class': self._class,
            'title': self._title,
            'state': self._state,
            'date': self._date,
        }

    def api_json(self):
        return {
            'id': self.str_id,
            'class': self._class,
            'title': self._title,
            'state': self._state,
            'date': self._date,
        }


class TicketHandle:
    ticket = None

    def __init__(self, ticket_id):
        ticket = ticket_id

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
        # Todo
        return web.Response(text='Hello, world')

    @staticmethod
    async def apply(request):
        """
        申请一张新的票券
        :param request:
        :return:
        """
        # Todo 用户本周已领取票券数量限制
        data = await request.json()
        ticket = Ticket(**data)
        db = request.app['db']
        res = await db.ticket.insert_one(ticket.mongo_json())
        if res.inserted_id is None:
            pass
        data['id'] = str(res.inserted_id)
        return web.json_response(data)

    @staticmethod
    async def list(request):
        """
        获取用户拥有的票券
        :param request:
        :return:
        """
        # Todo 增加用户识别字段
        db = request.app['db']
        data = {
            'count': 0,
            'items': []
        }
        this_week_start = get_this_week_start().strftime('%Y-%m-%d')
        this_week_end = get_this_week_end().strftime('%Y-%m-%d')
        cursor = db.ticket.find({'date': {'$gte': this_week_start, '$lte': this_week_end}})
        # for ticket in await cursor.to_list(length=100):
        async for ticket_doc in cursor:
            ticket = Ticket(**ticket_doc)
            data['items'].append(ticket.api_json())
            data['count'] += 1
            pass
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
