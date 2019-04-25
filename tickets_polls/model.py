"""
filename: model.py
datetime: 2019-04-25
author: muumlover
"""

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

    @property
    def object_id(self):
        if self._id is None:
            return
        return self._id

    @object_id.setter
    def object_id(self, id_):
        self._id = ObjectId(id_)

    @property
    def str_id(self):
        if self._id is None:
            return ''
        return str(self._id)

    @property
    def create_time(self):
        if self._id is None:
            return None
        return self._id.generation_time.astimezone()

    def mongo_json(self):
        return {key: self.__getattribute__('_{}'.format(key)) for key in self.fled_list}

    def api_json(self):
        json = {'id': self.str_id}
        for key in self.fled_list:
            value = self.__getattribute__('_{}'.format(key))
            if value is None:
                pass
            elif type(value) == ObjectId:
                value = str(value)
            json.update({key: value})
        return json


class Ticket(Model):
    fled_list = ['class', 'title', 'date', 'state', 'user']
    fled_default = {
        'state': 'unused'
    }

    @property
    def user(self):
        return self.__getattribute__('_user')

    @user.setter
    def user(self, value):
        """

        :type value: User
        """
        self.__setattr__('_user', value.object_id)


class User(Model):
    fled_list = ['open-id']
    fled_default = {}

    @staticmethod
    async def find_or_insert_one(db, data):
        user_mongo = await db.user.find_one(data)
        if user_mongo is None:
            user = User(**data)
            res = await db.user.insert_one(user.mongo_json())
            if res.inserted_id is None:
                pass
            user.object_id = res.inserted_id
        else:
            user = User(**user_mongo)
        return user
