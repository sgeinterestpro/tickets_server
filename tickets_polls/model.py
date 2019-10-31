"""
filename: model.py
datetime: 2019-04-25
author: muumlover
"""
import uuid
from datetime import datetime

from bson import ObjectId


def setup_model(app):
    Model._db = app['db']


class Model:
    """
    数据对象
    """
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

    def __getitem__(self, item):
        return self.__getattribute__('_{}'.format(item))

    def __setitem__(self, key, value):
        return self.__setattr__('_{}'.format(key), value)

    @property
    def mongo_id(self):
        if self._id is None:
            return
        return self._id

    @property
    def json_id(self):
        if self._id is None:
            return ''
        return str(self._id)

    # @property
    # def create_time(self):
    #     if self._id is None:
    #         return None
    #     return self._id.generation_time.astimezone()

    @classmethod
    async def m_find_one(cls, data):
        if '_id' in data and ObjectId.is_valid(data['_id']):
            data['_id'] = ObjectId(data['_id'])
        doc = await Model._db[cls.collection_name].find_one(data)
        return cls(**(doc or {}))

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await Model._db[cls.collection_name].find_one(*args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await Model._db[cls.collection_name].insert_one(*args, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await Model._db[cls.collection_name].update_one(*args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await Model._db[cls.collection_name].delete_one(*args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return Model._db[cls.collection_name].find(*args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await Model._db[cls.collection_name].insert_many(*args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await Model._db[cls.collection_name].count_documents(*args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return Model._db[cls.collection_name].aggregate(*args, **kwargs)

    def to_object(self, include_id=False):
        json = {}
        if include_id:
            json.update({'_id': self.mongo_id})
        for key in self.fled_list:
            json.update({key: self.__getattribute__('_{}'.format(key))})
        return json

    def to_json(self):
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
    ]
    fled_default = {
        'state': 'default'
    }


class Ticket(Model):
    collection_name = 'ticket'
    fled_list = [
        'class',
        'state',
        'expiry_date',
        'raiser', 'raise_time',
        'purchaser', 'purch_time',
        'checker', 'check_time',
        'deleter', 'delete_time',
        'overdue_time'
    ]
    fled_default = {
        'state': 'default'
    }

    @staticmethod
    async def generate(raiser, raise_count):
        ticket_id_base = 'SGE_{time}%s'.format(time=datetime.now().strftime('%Y%m%d'))
        raise_time = datetime.now()
        new_ticket_list = [Ticket(_id=ticket_id_base % (uuid.uuid1().hex.upper()),
                                  raiser=raiser.mongo_id,
                                  raise_time=raise_time).to_object(True) for _ in range(raise_count)]
        res = await Ticket.insert_many(new_ticket_list)
        return res.inserted_ids


class TicketCheck(Model):
    collection_name = 'ticket_check'
    fled_list = []
    fled_default = {}


class TicketLog(Model):
    collection_name = 'ticket_log'
    fled_list = []
    fled_default = {}


class User(Model):
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
        'init_id'
    ]
    fled_default = {
    }

    @staticmethod
    async def find_or_insert_one(data):
        user_mongo = await User.find_one(data)
        if user_mongo is None:
            user = User(**data)
            res = await User.insert_one(user.to_object())
            if res.inserted_id is None:
                pass
            user['id'] = res.inserted_id
        else:
            user = User(**user_mongo)
        return user


class UserInit(Model):
    collection_name = 'user_init'
    fled_list = [
        'real_name',
        'department',
        'email',
        'phone',
        'work_no',
        'sports',
        'role'
    ]
    fled_default = {
        'sports': [],
        'role': []
    }

    @property
    def is_admin(self):
        return 'admin' in self['role']

    @staticmethod
    async def m_find_one_by_user(user):
        return await UserInit.m_find_one({'_id': user['init_id']})


class Email(Model):
    collection_name = 'user_init'
    fled_list = [
        'host',
        'port',
        'user',
        'pass',
        'limit',
        'used'
    ]
    fled_default = {
        'limit': 0,
        'used': 0
    }

    @staticmethod
    async def use_one():
        cursor = Email.find()
        async for server in cursor:
            if server.get('used', 0) < server.get('limit', 0):
                await Email.update_one({
                    'user': server['user']
                }, {'$set': {
                    'used': server.get('used', 0) + 1
                }})
                return server
