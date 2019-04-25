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
    def str_id(self):
        return str(self._id)

    @str_id.setter
    def str_id(self, id_):
        self._id = ObjectId(id_)

    @property
    def create_time(self):
        return self._id.generation_time.astimezone()

    def mongo_json(self):
        return {key: self.__getattribute__('_{}'.format(key)) for key in self.fled_list}

    def api_json(self):
        json = {'id': self.str_id}
        json.update(self.mongo_json())
        return json


class Ticket(Model):
    fled_list = ['class', 'title', 'date', 'state']
    fled_default = {
        'state': 'unused'
    }


class User(Model):
    fled_list = ['open-id']
    fled_default = {}
