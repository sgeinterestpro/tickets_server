"""
filename: model.py
datetime: 2019-04-25
author: muumlover
"""
import uuid
from datetime import datetime
from typing import Awaitable, Optional, AsyncIterable

from aiohttp.abc import Application
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCursor
from pymongo.results import UpdateResult, InsertManyResult, DeleteResult, InsertOneResult

from unit import date_week_start, date_week_end, week_zh


def setup_model(app: Application) -> None:
    if 'db' not in app:
        raise Exception('需要初始化数据库')
    Model._db = app['db']
    Model._config = app['config']


class ModelCursor(object):
    cls: type
    cursor: AsyncIOMotorCursor

    def __init__(self, cls: type, cursor: AsyncIOMotorCursor):
        self.cls = cls
        self.cursor = cursor
        self.aiter = None

    def __aiter__(self):
        self.aiter = self.cursor.__aiter__()
        return self

    async def __anext__(self) -> 'Model':
        doc = await self.aiter.__anext__()
        return self.cls(**(doc or {}))

    def sort(self, *args, **kwargs) -> 'ModelCursor':
        return ModelCursor(self.cls, self.cursor.sort(*args, **kwargs))


class Model(object):
    """
    数据对象
    """
    _config = None
    _db = None
    _id = None
    collection_name = None
    fled_list = []
    fled_default = {}

    def __new__(cls, *args, **kwargs):
        if kwargs:
            return super().__new__(cls, *args)

    def __init__(self, **kwargs) -> None:
        if '_id' in kwargs:
            self._id = kwargs['_id']
        for key in self.fled_list:
            if key not in kwargs:
                self.__setattr__('_{}'.format(key), self.fled_default.get(key, None))
            else:
                self.__setattr__('_{}'.format(key), kwargs[key])

    def __eq__(self, other: 'Model'):
        return self.mongo_id == other.mongo_id

    def __getitem__(self, item):
        return self.__getattribute__('_{}'.format(item))

    def __setitem__(self, key, value):
        return self.__setattr__('_{}'.format(key), value)

    def get(self, key, default=None):
        return self[key] if key in self.fled_list else default

    @property
    def mongo_id(self) -> Optional[ObjectId]:
        if self._id is None:
            return
        return self._id

    @property
    def json_id(self) -> str:
        if self._id is None:
            return ''
        return str(self._id)

    # @property
    # def create_time(self):
    #     if self._id is None:
    #         return None
    #     return self._id.generation_time.astimezone()

    @classmethod
    async def find_one(cls, data) -> 'Model':
        """
        
        :type data: dict
        :rtype: Awaitable[Model]
        :param data: 
        :return: 
        """
        if '_id' in data and ObjectId.is_valid(data['_id']):
            data['_id'] = ObjectId(data['_id'])
        doc = await Model._db[cls.collection_name].find_one(data)
        return cls(**(doc or {}))

    @classmethod
    def find(cls, *args, **kwargs) -> ModelCursor:
        return ModelCursor(cls, Model._db[cls.collection_name].find(*args, **kwargs))

    @classmethod
    def aggregate(cls, *args, **kwargs) -> AsyncIterable[dict]:
        return Model._db[cls.collection_name].aggregate(*args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs) -> InsertOneResult:
        return await Model._db[cls.collection_name].insert_one(*args, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs) -> UpdateResult:
        return await Model._db[cls.collection_name].update_one(*args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs) -> DeleteResult:
        return await Model._db[cls.collection_name].delete_one(*args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs) -> InsertManyResult:
        return await Model._db[cls.collection_name].insert_many(*args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs) -> UpdateResult:
        return await Model._db[cls.collection_name].update_many(*args, **kwargs)

    @classmethod
    async def count(cls, *args, **kwargs) -> int:
        """

        :rtype: int
        """
        return await Model._db[cls.collection_name].count_documents(*args, **kwargs)

    def to_object(self, include_id: bool = False) -> dict:
        json = {}
        if include_id:
            json.update({'_id': self.mongo_id})
        for key in self.fled_list:
            json.update({key: self.__getattribute__('_{}'.format(key))})
        return json

    def to_json(self) -> dict:
        json = {'_id': self.json_id}
        for key in self.fled_list:
            value = self.__getattribute__('_{}'.format(key))
            if value is None:
                pass
            elif type(value) == ObjectId:
                value = str(value)
            elif type(value) == datetime:
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            json.update({key: value})
        return json


class Captcha(Model):
    collection_name = 'captcha'
    fled_list = [
        'captcha',
        'email',
        'user_id',
        'url',
    ]
    fled_default = {}


class Message(Model):
    class State:
        admin_check = 'admin_check'
        notice = 'notice'

    class Operation:
        ticket_generate = 'ticket_generate'

    collection_name = 'message'
    fled_list = [
        'operation',
        'operator',
        'checker',
        'content',
        'params',
        'state',
        'time',
        'type',
    ]
    fled_default = {
        'state': 'default',
    }


class Sport(Model):
    collection_name = 'sport'
    fled_list = [
        'item',
        'day',
        'time',
    ]
    fled_default = {
        'day': [],
    }


class Ticket(Model):
    collection_name = 'ticket'
    fled_list = [
        'class',
        'state',
        'batch',
        'expiry_date',
        'raiser', 'raise_time',
        'purchaser', 'purch_time',
        'checker', 'check_time',
        'deleter', 'delete_time',
        'overdue_time',
    ]
    fled_default = {
        'state': 'default',
    }

    @property
    def class_name(self):
        sport_map = self._config.get('ticket', {}).get('sport', {})
        return sport_map.get(self['class'], '异常项目')

    @staticmethod
    async def generate(raiser, raise_count, checker=None):
        ticket_id_base = 'SGE_{time}%s'.format(time=datetime.now().strftime('%Y%m%d'))
        batch_id = (ticket_id_base % (uuid.uuid1().hex.upper()))[4:20]
        raise_time = datetime.now()
        batch_res = await TicketBatch.insert_one({'_id': batch_id,
                                                  'raiser': raiser.mongo_id,
                                                  'raise_time': raise_time,
                                                  'raise_count': raise_count,
                                                  'checker': checker, })
        new_ticket_list = [Ticket(_id=ticket_id_base % (uuid.uuid1().hex.upper()),
                                  batch=batch_res.inserted_id,
                                  raiser=raiser.mongo_id,
                                  raise_time=raise_time).to_object(True) for _ in range(raise_count)]
        res = await Ticket.insert_many(new_ticket_list)
        return res.inserted_ids

    @staticmethod
    async def week_count(user_id, sport_item=None):
        this_week_start = date_week_start().strftime('%Y-%m-%d')
        this_week_end = date_week_end().strftime('%Y-%m-%d')
        query = {
            'purchaser': user_id,
            'expiry_date': {
                '$gte': this_week_start,
                '$lte': this_week_end
            },
            'state': 'verified',
        }
        if sport_item is not None:
            query.update({
                'class': sport_item,
            })
        count = await Ticket.count(query)
        return count

    @staticmethod
    async def today_count(user_id, sport_item=None):
        date_now = datetime.now().strftime('%Y-%m-%d')
        query = {
            'purchaser': user_id,
            'expiry_date': {
                '$gte': date_now,
                '$lte': date_now
            },
            'state': 'verified',
        }
        if sport_item is not None:
            query.update({
                'class': sport_item,
            })
        count = await Ticket.count(query)
        return count


class TicketCheck(Model):
    collection_name = 'ticket_check'
    fled_list = [
        'checked_date',
        'check_time',
        'all',
        'default',
        'valid',
        'verified',
        'expired',
        'delete',
    ]
    fled_default = {}


class TicketLog(Model):
    collection_name = 'ticket_log'
    fled_list = [
        'init_id',
        'option',
        'ticket_id',
    ]
    fled_default = {}


class TicketBatch(Model):
    collection_name = 'ticket_batch'
    fled_list = [
        'raiser',
        'raise_time',
        'raise_count',
        'checker',
    ]
    fled_default = {}


class User(Model):
    """
    微信账号
    """
    collection_name = 'user'
    fled_list = [
        'wx_open_id',
        'avatarUrl',
        'city',
        'country',
        'gender',
        'language',
        'nickName',
        'province',
        'init_id',
    ]
    fled_default = {}

    @staticmethod
    async def find_or_insert_one(data):
        user = await User.find_one(data)
        if not user:
            user = User(**data)
            res = await User.insert_one(user.to_object())
            if res.inserted_id is None:
                pass
            user['id'] = res.inserted_id
        return user


class UserInit(Model):
    """
    人员账号
    """
    collection_name = 'user_init'
    fled_list = [
        'real_name',
        'work_no',
        'department',
        'email',
        'phone',
        'sports',
        'role',
        'state',
    ]
    fled_default = {
        'sports': [],
        'role': [],
    }

    def role_check(self, role) -> bool:
        if not self['role']:
            self['role'] = ['user']
        return role in self['role']

    async def get_sport(self):
        weekday = datetime.now().isoweekday()
        today_sports = {}
        sport: Sport

        async for sport in Sport.aggregate([
            {'$group': {'_id': '$item', 'item': {'$last': "$item"}, 'day': {'$push': '$day'}}}
        ]):
            b_join = sport['item'] in self['sports']
            b_open = weekday in sport['day']
            b_used = await Ticket.today_count(self.mongo_id, sport['item']) != 0
            if b_join:
                if b_open:
                    if b_used:
                        message = '以达到此项目今日打卡上限'
                    else:
                        sport_now = await Sport.find_one({'item': sport['item'], 'day': weekday})
                        message = f'今日[{", ".join("-".join(ts) for ts in sport_now["time"])}]可用'
                else:
                    sports_iter = Sport.find({'item': sport['item']})
                    sports_desc = [(s['day'], ','.join('-'.join(t) for t in s['time'])) async for s in sports_iter]
                    message = "\n".join([f"每周{week_zh(d)}[{t}]" for d, t in sports_desc])
            else:
                message = '未加入到该小组'
            today_sports[sport['item']] = {
                'enable': b_join and b_open and not b_used,
                'joined': b_join,
                'message': message
            }
        return today_sports

    @staticmethod
    async def find_one_by_user(user: User):
        return await UserInit.find_one({'_id': user['init_id'] if user else None})


class OperateLog(Model):
    collection_name = 'operate_log'
    fled_list = [
        'operator_id',
        'option',
        'param',
    ]
    fled_default = {}


class Email(Model):
    collection_name = 'user_init'
    fled_list = [
        'host',
        'port',
        'user',
        'pass',
        'limit',
        'used',
    ]
    fled_default = {
        'limit': 0,
        'used': 0,
    }

    @staticmethod
    async def use_one():
        cursor = Email.find()
        server: Model
        async for server in cursor:
            if server.get('used', 0) < server.get('limit', 0):
                await Email.update_one({
                    'user': server['user']
                }, {'$set': {
                    'used': server.get('used', 0) + 1
                }})
                return server
