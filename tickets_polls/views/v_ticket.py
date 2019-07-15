"""
filename: v_ticket.py
datetime: 2019-04-22
author: muumlover
"""
import uuid
from datetime import datetime, timedelta

from aiohttp import web
from bson import ObjectId

from model import Ticket, User
from unit import date_week_start, date_week_end, date_month_start


class TicketHandles:

    @staticmethod
    async def ticket_package(request):
        """
        获取用户拥有的票券
        :param request:
        :return:
        """
        db = request.app['db']
        user = await User.find_or_insert_one(db, {'wx_open_id': request['open-id']})
        this_week_start = date_week_start().strftime('%Y-%m-%d')
        this_week_end = date_week_end().strftime('%Y-%m-%d')
        cursor = db.ticket.find({
            'purchaser': user.object_id,
            'expiry_date': {'$gte': this_week_start, '$lte': this_week_end}
        })

        data = {'count': 0, 'items': []}
        # for ticket in await cursor.to_list(length=100):
        async for ticket_doc in cursor:
            ticket = Ticket(**ticket_doc)
            data['items'].append(ticket.to_json())
            data['count'] += 1

        return web.json_response(data)

    @staticmethod
    async def ticket_purchase(request):
        """
        申请领取一张票券
        :param request:
        :return:
        """
        db = request.app['db']

        # 获取用户信息
        user = await User.find_or_insert_one(db, {'wx_open_id': request['open-id']})
        data = await request.json()

        # 检查本周领取限额
        this_week_start = date_week_start().strftime('%Y-%m-%d')
        this_week_end = date_week_end().strftime('%Y-%m-%d')
        count = await db.ticket.count_documents({
            'purchaser': user.object_id,
            'purch_time': {'$gte': this_week_start, '$lte': this_week_end}
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

        # 领取票券
        # ticket = Ticket(**data)
        # ticket.user_id = user.object_id
        # res = await db.ticket.insert_one(ticket.to_object())
        new_value = {
            'class': data['class'],
            'state': 'valid',
            'purchaser': user.object_id,
            'purch_time': datetime.now(),
            'expiry_date': data['date']
        }
        res = await db.ticket.update_one({
            'state': 'default'
        }, {
            '$set': new_value
        })
        if res.matched_count == 0:
            return web.json_response({'code': -1, 'message': '没有可领取的票券'})
        if res.modified_count == 0:
            return web.json_response({'code': -2, 'message': '更新票券信息失败'})
        new_ticket_data = await db.ticket.find_one(new_value)
        new_ticket = Ticket(**new_ticket_data)
        _ = await db.ticket_log.insert_one(
            {'user_id': user.object_id, 'option': 'purchase', 'ticket_id': new_ticket.json_id})
        return web.json_response({'code': 0, 'message': '票券领取成功'})

    @staticmethod
    async def ticket_refund(request):
        """
        申请退回一张票券
        :param request:
        :return:
        """
        # todo 判断票券状态是否为已使用或已过期
        db = request.app['db']
        user = await User.find_or_insert_one(db, {'wx_open_id': request['open-id']})
        data = await request.json()
        if 'ticket_id' not in data:
            return web.json_response({'code': -2, 'message': '请求参数错误'})

        res = await db.ticket.update_one({
            '_id': data['ticket_id'],
            'state': 'valid',
            'purchaser': user.object_id
        }, {
            '$set': {
                'class': None,
                'state': 'default',
                'purchaser': None,
                'purch_time': None,
                'expiry_date': None
            }
        })

        if res.matched_count == 0:
            return web.json_response({'code': -2, 'message': '找不到对应的票券'})
        if res.modified_count == 0:
            return web.json_response({'code': -2, 'message': '更新票券信息失败'})
        _ = await db.ticket_log.insert_one(
            {'user_id': user.object_id, 'option': 'refund', 'ticket_id': data['ticket_id']})
        return web.json_response({'code': 0, 'message': '票券删除成功'})

    @staticmethod
    async def ticket_inspect(request):
        """
        获取 ticket 信息
        :param request:
        :return:
        """
        db = request.app['db']
        data = await request.json()
        if 'ticket_id' not in data:
            return web.json_response({'code': -2, 'message': '请求参数错误'})

        ticket_doc = await db.ticket.find_one({
            '_id': data['ticket_id'],
        })
        if ticket_doc is None:
            return web.json_response({'code': -1, 'message': '未找到此票券'})

        ticket = Ticket(**ticket_doc)

        if ticket['state'] == 'default':
            return web.json_response({'code': -1, 'message': '票券未激活'})
        if ticket['state'] == 'verified':
            return web.json_response({'code': -1, 'message': '票券已被使用'})
        if ticket['state'] == 'expired':
            return web.json_response({'code': -1, 'message': '票券已过期'})
        if ticket['state'] == 'invalid':
            return web.json_response({'code': -1, 'message': '票券已作废'})
        if ticket['state'] != 'valid':
            return web.json_response({'code': -1, 'message': '票券状态异常'})
        date_now = datetime.now().strftime('%Y-%m-%d')
        if ticket['expiry_date'] < date_now:
            return web.json_response({'code': -1, 'message': '票券已过期'})
        if ticket['expiry_date'] > date_now:
            return web.json_response({'code': -1, 'message': '票券未生效'})

        user_doc = await db.user.find_one({
            '_id': ticket['purchaser']
        })
        user = User(**user_doc)
        return web.json_response({'code': 0, 'message': '票券状态核验通过', 'ticket': ticket.to_json(), 'user': user.to_json()})

    @staticmethod
    async def ticket_checked(request):
        """
        使用 ticket
        :param request:
        :return:
        """
        # Todo
        db = request.app['db']
        data = await request.json()
        if 'ticket_id' not in data:
            return web.json_response({'code': -2, 'message': '请求参数错误'})

        ticket_doc = await db.ticket.find_one({
            '_id': data['ticket_id'],
        })
        if ticket_doc is None:
            return web.json_response({'code': -1, 'message': '票券不存在'})
        if ticket_doc['state'] != 'valid':
            return web.json_response({'code': -1, 'message': '票券状态异常'})
        date_now = datetime.now().strftime('%Y-%m-%d')
        if ticket_doc['expiry_date'] != date_now:
            return web.json_response({'code': -1, 'message': '票券日期不正确'})

        user = await User.find_or_insert_one(db, {'wx_open_id': request['open-id']})
        res = await db.ticket.update_one({
            '_id': data['ticket_id']
        }, {
            '$set': {
                'state': 'verified',
                'checker': user.object_id,
                'check_time': datetime.now()
            }
        })

        if res.matched_count == 0:
            return web.json_response({'code': -2, 'message': '找不到对应的票券'})
        if res.modified_count == 0:
            return web.json_response({'code': -2, 'message': '更新票券信息失败'})
        _ = await db.ticket_log.insert_one(
            {'user_id': user.object_id, 'option': 'checked', 'ticket_id': data['ticket_id']})
        return web.json_response({'code': 0, 'message': '票券检票成功'})

    @staticmethod
    async def ticket_generate(request):
        db = request.app['db']
        user = await User.find_or_insert_one(db, {'wx_open_id': request['open-id']})
        data = await request.json()
        if 'count' not in data:
            return web.json_response({'code': -2, 'message': '请求参数错误'})
        ticket_id_base = 'SGE_{time}%s'.format(time=datetime.now().strftime('%Y%m%d'))
        raise_time = datetime.now()
        new_ticket_list = [Ticket(_id=ticket_id_base % (uuid.uuid1().hex.upper()),
                                  raiser=user.object_id,
                                  raise_time=raise_time).to_object(True) for _ in range(data['count'])]
        res = await db.ticket.insert_many(new_ticket_list)
        if len(res.inserted_ids) == 0:
            return web.json_response({'code': -3, 'message': '生成票券失败'})
        return web.json_response({'code': 0, 'message': '生成票券成功', 'data': data})

    @staticmethod
    async def ticket_usage(request):
        db = request.app['db']
        user = await User.find_or_insert_one(db, {'wx_open_id': request['open-id']})
        this_month_start = date_month_start().strftime('%Y-%m-%d')
        this_date_now = datetime.now().strftime('%Y-%m-%d')
        default_count = await db.ticket.count_documents({
            'state': 'default',
        })
        valid_count = await db.ticket.count_documents({
            'state': 'valid',
            'expiry_date': {'$gte': this_month_start}
        })
        verified_count = await db.ticket.count_documents({
            'state': 'verified',
            'expiry_date': {'$gte': this_month_start}
        })
        expired_count = await db.ticket.count_documents({
            'state': 'expired',
            'expiry_date': {'$gte': this_month_start}
        })
        invalid_count = await db.ticket.count_documents({
            'state': 'invalid',
            'expiry_date': {'$gte': this_month_start}
        })
        return web.json_response({'code': 0, 'data': {
            'default': default_count,
            'active': valid_count + verified_count + expired_count + invalid_count,
            'valid': valid_count,
            'verified': verified_count,
            'expired': expired_count,
            'invalid': invalid_count
        }})

    @staticmethod
    async def ticket_log(request):
        """
        获取票券记录
        :param request:
        :return:
        """
        db = request.app['db']
        data = await request.json()
        skip_count = data.get('skip', 0)
        limit_count = data.get('limit', 5)
        match = {'$match': {'ticket_id': {'$ne': None}}}
        # 按时间排序记录
        sort = {'$sort': {'_id': -1}}
        skip = {'$skip': skip_count}
        limit = {'$limit': limit_count}
        # 联合查询票券信息表
        lookup_ticket = {
            '$lookup': {
                'from': 'ticket',
                'localField': 'ticket_id',
                'foreignField': '_id',
                'as': 'tickets'
            }
        }
        # 联合查询用户信息表
        lookup_user = {
            '$lookup': {
                'from': 'user',
                'localField': 'user_id',
                'foreignField': '_id',
                'as': 'users'
            }
        }
        # 转换查询结果列表为数据对象
        add_fields = {
            '$addFields': {
                'ticket': {'$arrayElemAt': ['$tickets', 0]},
                'user': {'$arrayElemAt': ['$users', 0]}
            }
        }
        # 联合查询用户工作信息表
        lookup_real = {
            '$lookup': {
                'from': 'user_init',
                'localField': 'user.init_id',
                'foreignField': '_id',
                'as': 'inits'
            }
        }
        # 转换查询结果列表为数据对象
        add_field_real = {
            '$addFields': {
                'init': {'$arrayElemAt': ['$inits', 0]}
            }
        }
        # 删除查询结果
        project = {'$project': {'tickets': 0, 'users': 0, 'inits': 0}}
        pipeline = [
            match,
            sort,
            skip,
            limit,
            lookup_ticket,
            lookup_user,
            add_fields,
            lookup_real,
            add_field_real,
            project
        ]
        cursor = db.ticket_log.aggregate(pipeline)
        data = {'count': 0, 'items': []}
        async for ticket_log_doc in cursor:
            '''目标数据格式
            {
                '_id': ObjectId('5d26e9e17e2fec35dd45fef6'),
                'user_id': ObjectId('5d25eee4f2a471d041f759b7'), 
                'option': 'purchase',
                'ticket_id': 'SGE201907105029500002',
                'ticket': {
                    '_id': 'SGE201907105029500002',
                    'class': 'basketball',
                    'state': 'expired',
                    'raiser': ObjectId('5d25eee4f2a471d041f759b7'),
                    'raise_time': datetime.datetime(2019, 7, 10, 21, 58, 15, 487000),
                    'purchaser': ObjectId('5d28638806e6e6b2a86bc85e'),
                    'purch_time': datetime.datetime(2019, 7, 13, 17, 4, 36, 78000),
                    'expiry_date': '2019-07-13',
                    'overdue_time': datetime.datetime(2019, 7, 14, 0, 0, 0, 7000), 
                    'checker': None,
                    'check_time': None
                }, 
                'user': {
                    '_id': ObjectId('5d25eee4f2a471d041f759b7'),
                    'wx_open_id': 'oZ2qW1Asmsq5MW__8yuK-IEueGIY',
                    'avatarUrl': 'https://wx.qlogo.cn/mmopen/vi_32/DYAIOgq15epMZYIBY5flW0YiaF2d57xx0a2fhyKtSKmyQZfBVsVvE1WWibu22PRyofvHAHJOXiavNBdSkQtibWK4ow/132',
                    'city': '',
                    'country': '',
                    'gender': 1,
                    'language': 'zh_CN', 
                    'nickName': '张三丰³',
                    'province': '',
                    'init_id': ObjectId('5d281c90e8834258726aa12c')
                },
                'init': {
                    '_id': ObjectId('5d281c90e8834258726aa12c'), 
                    'email': 'zhangsan@qq.com',
                    'real_name': '张三', 
                    'phone': '13300330333', 
                    'work_no': '5433',
                    'role': ['user', 'admin', 'checker']
                }
            }
            '''
            data['items'].append({
                'option': ticket_log_doc.get('option', None),
                'time': str(ticket_log_doc.get('_id', None).generation_time.astimezone()),
                'ticket_id': ticket_log_doc.get('ticket_id', None),
                'ticket_class': ticket_log_doc.get('ticket', {}).get('class', None),
                'real_name': ticket_log_doc.get('init', {}).get('real_name', None),
            })
            data['count'] += 1

        return web.json_response(data)

    @staticmethod
    async def ticket_check_log(request):
        db = request.app['db']
        # user = await User.find_or_insert_one(db, {'wx_open_id': request['open-id']})
        data = await request.json()
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        date_start = datetime.strptime(date, '%Y-%m-%d')
        date_end = datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)
        cursor = db.ticket.find({
            'check_time': {'$gte': date_start, '$lte': date_end}
        })

        data = {'count': 0, 'items': []}
        # for ticket in await cursor.to_list(length=100):
        async for ticket_doc in cursor:
            ticket = Ticket(**ticket_doc)
            data['items'].append(ticket.to_json())
            data['count'] += 1

        return web.json_response(data)


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
            '_id': ticket['purchaser']
        })
        user = User(**user_doc)
        return web.json_response({'code': 0, 'ticket': ticket.to_json(), 'user': user.to_json()})

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
            return web.json_response({'code': -1, 'message': '票券不存在'})
        if ticket_doc['state'] == 'used':
            return web.json_response({'code': -1, 'message': '票券已被使用'})
        if ticket_doc['state'] == 'expired':
            return web.json_response({'code': -1, 'message': '票券已过期'})
        if ticket_doc['state'] != 'unused':
            return web.json_response({'code': -1, 'message': '票券状态异常'})
        date_now = datetime.now().strftime('%Y-%m-%d')
        if ticket_doc['date'] < date_now:
            return web.json_response({'code': -1, 'message': '票券已过期'})
        if ticket_doc['date'] > date_now:
            return web.json_response({'code': -1, 'message': '票券未生效'})

        user = await User.find_or_insert_one(db, {'wx_open_id': request['open-id']})
        res = await db.ticket.update_one({
            '_id': ObjectId(self.ticket_id)
        }, {
            '$set': {'state': 'used', 'user': user.object_id}
        })

        if res.matched_count == 0:
            return web.json_response({'code': -2, 'message': '票券不存在'})
        if res.modified_count == 0:
            return web.json_response({'code': -2, 'message': '票券已被使用'})
        return web.json_response({'code': 0, 'message': '状态更新成功'})

    async def delete(self, request):
        """
        删除 ticket
        :param request:
        :return:
        """
        # todo 判断票券状态是否为已使用或已过期
        db = request.app['db']
        user = await User.find_or_insert_one(db, {'wx_open_id': request['open-id']})
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
        user = await User.find_or_insert_one(db, {'wx_open_id': request['open-id']})
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
        ticket.purchaser = user.object_id
        res = await db.ticket.insert_one(ticket.to_object())
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
        user = await User.find_or_insert_one(db, {'wx_open_id': request['open-id']})
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
            data['items'].append(ticket.to_json())
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
