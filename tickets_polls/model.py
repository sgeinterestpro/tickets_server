"""
filename: model.py
datetime: 2019-04-25
author: muumlover
"""

from datetime import datetime

from bson import ObjectId


class Model:
    """
    数据对象
    """
    _id = None
    fled_list = []
    fled_default = {}

    def __init__(self, **kwargs) -> None:
        if '_id' in kwargs:
            self._id = kwargs['_id']
        for key in self.fled_list:
            if key not in kwargs:
                self.__setattr__('_{}'.format(key), self.fled_default.setdefault(key, None))
            else:
                self.__setattr__('_{}'.format(key), kwargs[key])

    def __getitem__(self, item):
        return self.__getattribute__('_{}'.format(item))

    def __setitem__(self, key, value):
        return self.__setattr__('_{}'.format(key), value)

    @property
    def object_id(self):
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

    def to_object(self, include_id=False):
        json = {}
        if include_id:
            json.update({'_id': self.object_id})
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
                value = str(value)
            json.update({key: value})
        return json


class Ticket(Model):
    fled_list = ['class', 'state', 'raiser', 'raise_time', 'purchaser', 'purch_time', 'expiry_date', 'overdue_time',
                 'checker', 'check_time']
    fled_default = {
        'class': None,
        'state': 'default',
        'raiser': None,
        'raise_time': None,
        'purchaser': None,
        'purch_time': None,
        'expiry_date': None,
        'overdue_time': None,
        'checker': None,
        'check_time': None
    }


class User(Model):
    fled_list = ['wx_open_id']
    fled_default = {}

    @staticmethod
    async def find_or_insert_one(db, data):
        user_mongo = await db.user.find_one(data)
        if user_mongo is None:
            user = User(**data)
            res = await db.user.insert_one(user.to_object())
            if res.inserted_id is None:
                pass
            user['id'] = res.inserted_id
        else:
            user = User(**user_mongo)
        return user
