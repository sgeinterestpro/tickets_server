"""
filename: v_ticket.py
datetime: 2019-04-22
author: muumlover
"""
import base64
import warnings
from datetime import datetime, timedelta

import pymongo
from aiohttp import web
from aiohttp.abc import Request, StreamResponse
from cryptography.hazmat.primitives.asymmetric import padding

from middleware import auth_need, Auth
from model import Ticket, User, UserInit, TicketLog, Message, TicketBatch, Sport
from unit import date_week_start, date_week_end, date_month_start, date_month_end


class TicketHandles:

    @staticmethod
    @auth_need(Auth.user)
    async def ticket_package(request: Request) -> StreamResponse:
        """
        获取用户拥有的票券
        :param request:
        :return:
        """
        this_week_start = date_week_start().strftime('%Y-%m-%d')
        this_week_end = date_week_end().strftime('%Y-%m-%d')
        cursor = Ticket.find({
            'state': {'$ne': 'default'},
            'purchaser': request['user'].mongo_id,
            'expiry_date': {'$gte': this_week_start, '$lte': this_week_end}
        })

        date_now = datetime.now().strftime('%Y-%m-%d')
        count, items = 0, []
        # for ticket in await cursor.to_list(length=100):
        async for ticket in cursor:
            if ticket['state'] == 'valid' and date_now > ticket['expiry_date']:
                ticket['state'] = 'expired'
            if ticket['state'] == 'delete':
                continue
            items.append(ticket.to_json())
            count += 1

        return web.json_response({'code': 0, 'message': '获取票券列表成功', 'count': count, 'items': items})

    @staticmethod
    @auth_need(Auth.user)
    async def ticket_purchase(request: Request) -> StreamResponse:
        """
        申请领取一张票券
        :param request:
        :return:
        """
        warnings.warn("some_old_function is deprecated", DeprecationWarning)

        # 获取用户信息
        data = await request.json()

        # 检查本周领取限额
        this_week_start = date_week_start().strftime('%Y-%m-%d')
        this_week_end = date_week_end().strftime('%Y-%m-%d')
        count = await Ticket.count({
            'purchaser': request['user'].mongo_id,
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
        new_value = {
            'class': data['class'],
            'state': 'valid',
            'purchaser': request['user'].mongo_id,
            'purch_time': datetime.now(),
            'expiry_date': data['date']
        }

        res = await Ticket.update_one({'state': 'default'}, {'$set': new_value})
        if res.matched_count == 0:
            return web.json_response({'code': -1, 'message': '没有可领取的票券'})
        if res.modified_count == 0:
            return web.json_response({'code': -3, 'message': '更新票券信息失败'})

        # 插入票券记录
        new_ticket = await Ticket.find_one(new_value)
        _ = await TicketLog.insert_one(
            {'init_id': request['user']['init_id'], 'option': 'purchase', 'ticket_id': new_ticket.json_id})

        return web.json_response({'code': 0, 'message': '票券领取成功'})

    @staticmethod
    @auth_need(Auth.user)
    async def ticket_sign_in(request: Request) -> StreamResponse:
        """
        签到打卡
        :param request:
        :return:
        """
        # 解析请求数据
        data = await request.json()
        if 'checker_id' not in data or 'class' not in data:
            return web.json_response({'code': -2, 'message': '请求参数错误'})

        checker_wx = None  # id数据转换前过渡
        # 获取扫描员
        checker = await UserInit.find_one({'_id': data['checker_id']})
        if not checker:  # 此处兼容已经打印好的二维码
            checker_wx = await User.find_one({'_id': data['checker_id']})
            if not checker_wx:
                return web.json_response({'code': -1, 'message': '站点信息不存在'})
            checker = await UserInit.find_one_by_user(checker_wx)
        if not checker:
            return web.json_response({'code': -1, 'message': '无效的运动站点'})
        if not checker.role_check('checker'):
            return web.json_response({'code': -1, 'message': '非法的运动站点'})

        if not checker_wx:  # id数据转换前过渡
            checker_wx = await User.find_one({'init_id': checker.mongo_id})  # id数据转换前过渡

        # 检查运动项目是否可用
        weekday = datetime.now().isoweekday()
        sport = await Sport.find_one({'item': data['class'], 'day': weekday})
        if not sport:
            return web.json_response({'code': -1, 'message': '今日不可领取该类型的票券'})

        # 检查是否满足时间限制
        time = datetime.now().strftime("%H:%M")
        for timespan in sport['time']:
            if timespan[0] <= time <= timespan[1]:
                break
        else:
            return web.json_response({'code': -1, 'message': '非指定活动时间'})

        # 检查运动项目领用权限
        if data['class'] not in request['user_init']['sports']:
            return web.json_response({'code': -1, 'message': '不能打卡其他组的运动项目'})

        # 检查本周领取限额
        if await Ticket.week_count(request['user'].mongo_id) >= 3:
            return web.json_response({'code': -1, 'message': '已超过本周领取限额'})

        # 检查当日是否已使用过该项目
        if await Ticket.today_count(request['user'].mongo_id, data['class']) >= 1:
            return web.json_response({'code': -1, 'message': '本日已打卡该项目，无法重复打卡'})

        # 领取票券
        check_time = datetime.now()
        new_value = {
            'class': data['class'],
            'state': 'verified',
            'purchaser': request['user'].mongo_id,
            'purch_time': check_time,
            'checker': checker_wx.mongo_id,  # id数据转换前过渡
            'check_time': check_time,
            'expiry_date': check_time.strftime('%Y-%m-%d')
        }

        # 更新票券信息
        res = await Ticket.update_one({'state': 'default'}, {'$set': new_value})
        if res.matched_count == 0:
            return web.json_response({'code': -1, 'message': '票券已被用光，请提醒管理员补充票券'})
        if res.modified_count == 0:
            return web.json_response({'code': -3, 'message': '签写票券信息失败'})

        # 生成票券使用记录
        new_ticket = await Ticket.find_one(new_value)
        _ = await TicketLog.insert_one(
            {'init_id': request['user']['init_id'], 'option': 'purchase', 'ticket_id': new_ticket.json_id}
        )
        check_time_show = check_time.strftime('%Y{}%m{}%d{} %H:%M:%S').format('年', '月', '日')
        return web.json_response({'code': 0, 'message': '运动打卡成功', 'data': {'time': check_time_show}})

    @staticmethod
    @auth_need(Auth.user)
    async def ticket_refund(request: Request) -> StreamResponse:
        """
        申请退回一张票券
        :param request:
        :return:
        """
        warnings.warn("some_old_function is deprecated", DeprecationWarning)
        # todo 判断票券状态是否为已使用或已过期
        data = await request.json()

        if 'ticket_id' not in data or not data['ticket_id']:
            return web.json_response({'code': -2, 'message': '请求参数错误'})

        ticket = await Ticket.find_one({'_id': data['ticket_id']})

        if ticket is None:
            return web.json_response({'code': -1, 'message': '无法删除不存在的票券'})

        if request['user'].mongo_id != ticket['purchaser']:
            return web.json_response({'code': -1, 'message': '无法删除他人的票券'})

        if ticket['state'] != 'valid':
            return web.json_response({'code': -1, 'message': '无法删除此状态的票券'})

        date_now = datetime.now().strftime('%Y-%m-%d')
        if date_now > ticket['expiry_date']:
            return web.json_response({'code': -1, 'message': '无法删除已过期票券'})

        # 检查本周删除限额
        count = await Ticket.count({
            'deleter': request['user'].mongo_id,
            'delete_time': {'$gte': date_week_start(), '$lte': date_week_end()}
        })
        if count >= 3:
            return web.json_response({'code': -1, 'message': '已超过本周最大删除数量'})

        res = await Ticket.update_one({
            '_id': data['ticket_id'],
            'state': 'valid',
            'purchaser': request['user'].mongo_id
        }, {
            '$set': {
                'state': 'delete',
                'deleter': request['user'].mongo_id,
                'delete_time': datetime.now(),
            }
        })

        if res.matched_count == 0:
            return web.json_response({'code': -3, 'message': '找不到对应的票券'})
        if res.modified_count == 0:
            return web.json_response({'code': -3, 'message': '更新票券信息失败'})
        _ = await TicketLog.insert_one(
            {'init_id': request['user']['init_id'], 'option': 'refund', 'ticket_id': data['ticket_id']})
        return web.json_response({'code': 0, 'message': '票券删除成功'})

    @staticmethod
    @auth_need(Auth.checker)
    async def ticket_inspect(request: Request) -> StreamResponse:
        """
        获取 ticket 信息
        :param request:
        :return:
        """
        warnings.warn("some_old_function is deprecated", DeprecationWarning)

        data = await request.json()

        if 'ticket_id' not in data or not data['ticket_id']:
            return web.json_response({'code': -2, 'message': '请求参数错误'})

        # 解密
        private_key = request.app['private_key']
        ticket_id_encrypt = base64.b64decode(data['ticket_id'])
        ticket_id = private_key.decrypt(ticket_id_encrypt, padding.PKCS1v15()).decode()

        ticket = await Ticket.find_one({
            '_id': ticket_id,
        })

        if ticket is None:
            return web.json_response({'code': -1, 'message': '未找到此票券'})

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

        purchaser = await User.find_one({
            '_id': ticket['purchaser']
        })
        purchaser_init = await UserInit.find_one({
            '_id': purchaser['init_id']
        })
        return web.json_response({
            'code': 0, 'message': '票券状态核验通过',
            'ticket': ticket.to_json(),
            'user': purchaser.to_json(),
            'init': purchaser_init.to_json()
        })

    @staticmethod
    @auth_need(Auth.checker)
    async def ticket_checked(request: Request) -> StreamResponse:
        """
        使用 ticket
        :param request:
        :return:
        """
        warnings.warn("some_old_function is deprecated", DeprecationWarning)

        # Todo
        data = await request.json()
        if 'ticket_id' not in data or not data['ticket_id']:
            return web.json_response({'code': -2, 'message': '请求参数错误'})

        # 解密
        private_key = request.app['private_key']
        ticket_id_encrypt = base64.b64decode(data['ticket_id'])
        ticket_id = private_key.decrypt(ticket_id_encrypt, padding.PKCS1v15()).decode()

        ticket = await Ticket.find_one({
            '_id': ticket_id,
        })
        if not ticket:
            return web.json_response({'code': -1, 'message': '票券不存在'})
        if ticket['state'] != 'valid':
            return web.json_response({'code': -1, 'message': '票券状态异常'})
        date_now = datetime.now().strftime('%Y-%m-%d')
        if ticket['expiry_date'] != date_now:
            return web.json_response({'code': -1, 'message': '票券日期不正确'})

        res = await Ticket.update_one({
            '_id': data['ticket_id']
        }, {
            '$set': {
                'state': 'verified',
                'checker': request['user'].mongo_id,
                'check_time': datetime.now()
            }
        })

        if res.matched_count == 0:
            return web.json_response({'code': -3, 'message': '找不到对应的票券'})
        if res.modified_count == 0:
            return web.json_response({'code': -3, 'message': '更新票券信息失败'})

        purchaser = await User.find_one({'_id': ticket['purchaser']})
        _ = await TicketLog.insert_one(
            {'init_id': purchaser['init_id'], 'option': 'checked', 'ticket_id': data['ticket_id']})

        return web.json_response({'code': 0, 'message': '票券检票成功'})

    @staticmethod
    @auth_need(Auth.admin)
    async def ticket_generate(request: Request) -> StreamResponse:
        data = await request.json()
        if 'count' not in data:
            return web.json_response({'code': -2, 'message': '请求参数错误'})
        try:
            data_count = int(data['count'])
        except ValueError:
            return web.json_response({'code': -2, 'message': '数量只能为十进制罗马数字'})

        # 改为需二次复核的方式
        _ = await Message.insert_one({
            'operation': Message.Operation.ticket_generate,
            'operator': request['user'].mongo_id,
            'checker': None,
            'content': f'{request["user_init"]["real_name"]}增发{data_count}张票券',
            'params': {'count': data_count},
            'state': 'valid',
            'time': datetime.now(),
            'type': Message.State.admin_check,
        })

        return web.json_response({'code': 0, 'message': '增发操作提交成功'})

    @staticmethod
    @auth_need(Auth.admin)
    async def ticket_usage(request: Request) -> StreamResponse:
        this_month_start = date_month_start().strftime('%Y-%m-%d')
        state_map = request.app['config'].get('ticket', {}).get('state', {})
        data = {}
        for state in state_map.keys():
            if state == 'default':
                count = await Ticket.count({
                    'state': state,
                })
            else:
                count = await Ticket.count({
                    'state': state,
                    'expiry_date': {'$gte': this_month_start}
                })
            data[state] = count
        return web.json_response({'code': 0, 'message': '获取票券数量信息成功', 'data': data})

    @staticmethod
    @auth_need(Auth.admin)
    async def ticket_batch(request: Request) -> StreamResponse:
        cursor = TicketBatch.find({}).sort([('raise_time', pymongo.DESCENDING)])
        count, items = 0, []
        ticket_batch: TicketBatch
        async for ticket_batch in cursor:
            available = await Ticket.count({
                'state': 'default',
                'batch': ticket_batch.mongo_id
            })
            item = ticket_batch.to_json()
            item['available'] = available
            item.pop('raiser')
            items.append(item)
            count += 1
            if available == 0:
                break
        return web.json_response({'code': 0, 'message': '获取票券批次列表成功', 'count': count, 'items': items})

    @staticmethod
    @auth_need(Auth.admin)
    async def ticket_log(request: Request) -> StreamResponse:
        """
        获取票券记录
        :param request:
        :return:
        """
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
                'from': 'user_init',
                'localField': 'init_id',
                'foreignField': '_id',
                'as': 'inits'
            }
        }
        # 转换查询结果列表为数据对象
        add_fields = {
            '$addFields': {
                'ticket': {'$arrayElemAt': ['$tickets', 0]},
                'init': {'$arrayElemAt': ['$inits', 0]}
            }
        }
        # 删除查询结果
        project = {'$project': {'tickets': 0, 'users': 0}}
        pipeline = [
            match,
            sort,
            skip,
            limit,
            lookup_ticket,
            lookup_user,
            add_fields,
            project
        ]

        count, items = 0, []
        count_all = await TicketLog.count({'ticket_id': {'$ne': None}})

        if count_all > 0:
            cursor = TicketLog.aggregate(pipeline)
            ticket_log_doc: dict
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
                real_name = ticket_log_doc.get('init', {}).get('real_name', None)
                ticket_id = ticket_log_doc.get('ticket_id', None)[:20]
                items.append({
                    'time': str(ticket_log_doc['_id'].generation_time.astimezone()),
                    'text': f'{real_name} 领取 {ticket_id}',
                })
                count += 1
        return web.json_response({'code': 0, 'message': '获取票券记录成功', 'count': count, 'items': items})

    @staticmethod
    @auth_need(Auth.checker)
    async def ticket_check_log(request: Request) -> StreamResponse:
        data = await request.json()
        start = data.get('start', None)
        end = data.get('end', start)
        if start is not None:
            try:
                date_start = datetime.strptime(start, '%Y-%m-%d')
                date_end = datetime.strptime(end, '%Y-%m-%d') + timedelta(days=1)
            except ValueError:
                return web.json_response({'code': -2, 'message': '日期输入错误'})
            cursor = Ticket.find({
                'check_time': {'$gte': date_start, '$lte': date_end},
            })
        else:
            date_start = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
            date_end = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d') + timedelta(days=1)
            cursor = Ticket.find({
                'checker': request['user'].mongo_id,
                'check_time': {'$gte': date_start, '$lte': date_end},
            })

        count, items = 0, []
        async for ticket in cursor:
            purchaser_init = await UserInit.find_one_by_user(await User.find_one({'_id': ticket['purchaser']}))
            checker_init = await UserInit.find_one_by_user(await User.find_one({'_id': ticket['checker']}))
            items.append({
                'id': f'票券编号：{ticket.json_id[:20]}',
                'user': f'运动人员：{purchaser_init["real_name"]}',
                'class': f'运动项目：{ticket.class_name}',
                'time': f'检票时间：{ticket["check_time"].strftime("%Y-%m-%d %H:%M:%S")}',
                'checker': f'检票人员：{checker_init["real_name"]}',
            })
            count += 1

        return web.json_response({'code': 0, 'message': '获取票券使用记录成功', 'count': count, 'items': items})

    @staticmethod
    @auth_need(Auth.checker)
    async def ticket_check_count(request: Request) -> StreamResponse:
        data = await request.json()
        start = data.get('start', datetime.now().strftime('%Y-%m-%d'))
        end = data.get('end', start)
        try:
            date_start = datetime.strptime(start, '%Y-%m-%d')
            date_end = datetime.strptime(end, '%Y-%m-%d') + timedelta(days=1)
        except [ValueError, TypeError]:
            return web.json_response({'code': -2, 'message': '日期输入错误'})

        items = [{
            'start_': date_week_start(),
            'end_': date_week_end(),
            'items': []
        }, {
            'start_': date_week_start(datetime.now() - timedelta(days=7)),
            'end_': date_week_end(datetime.now() - timedelta(days=7)),
            'items': []
        }, {
            'start_': date_month_start(),
            'end_': date_month_end(),
            'items': []
        }, {
            'start_': date_start,
            'end_': date_end,
            'items': []
        }]

        async for checker_init in UserInit.find({'role': {'$all': ['checker']}}):
            checker = await User.find_one({'init_id': checker_init.mongo_id})
            if checker is None:
                continue
            for item in items:
                item['items'].append({
                    'name': checker_init['real_name'],
                    'count': await Ticket.count({
                        'checker': checker.mongo_id,
                        'check_time': {'$gte': item['start_'], '$lte': item['end_']}
                    })
                })

        for item in items:
            item['count'] = len(item['items'])
            item['start'] = item.pop('start_').strftime('%Y-%m-%d')
            item['end'] = item.pop('end_').strftime('%Y-%m-%d')

        return web.json_response({
            'code': 0,
            'message': '获取票券使用记录成功',
            'items': items,
            'custom': {}
        })
