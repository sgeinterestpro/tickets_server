import pathlib
from urllib.parse import quote_plus

from bson import ObjectId
from pymongo import MongoClient

from config import load_config

count = 0
conf = load_config(str(pathlib.Path('..') / 'config' / 'polls.yaml'))
uri = 'mongodb://{}:{}/{}'.format(quote_plus(conf['database']['host']), conf['database']['port'],
                                  quote_plus(conf['database']['name']))
client = MongoClient(uri)
db = client.get_database(quote_plus(conf['database']['name']))
# 遍历数据库内的所有集合
for c in db.list_collection_names():
    # 遍历集合内的所有文档
    for d in db.get_collection(c).find({}):
        # 遍历文档内的所有字段
        for k, v in d.items():
            if k == '_id':
                continue
            if not isinstance(v, ObjectId):
                continue
            user = db.user.find_one({"_id": v})
            if user is not None:
                count += 1
                user_init = db.user_init.find_one({"_id": user['init_id']})
                print(f"{count:04d} {c:12s} {str(d['_id']):44s} {k:9s} {v} {user['init_id']} {user_init['real_name']}")
                db.get_collection(c).update_one({'_id': d['_id']}, {"$set": {k: user['init_id']}})
            else:
                user_init = db.user_init.find_one({"_id": v})
                if user_init is None:
                    print(f"[{count:04d}] {c:12s} {str(d['_id']):44s} {k:9s} {v}")
pass
