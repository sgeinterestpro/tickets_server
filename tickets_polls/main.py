import pathlib

import yaml
from aiohttp import web

from routes import setup_routes


def load_config(config_path):
    with open(config_path, 'r') as f:
        cfg = f.read()
        print(type(cfg))  # 读出来是字符串
        print(cfg)
        config = yaml.load(cfg, Loader=yaml.BaseLoader)  # 用load方法转字典
    return config


app = web.Application()
conf = load_config(str(pathlib.Path('.') / 'config' / 'polls.yaml'))
app['config'] = conf
setup_routes(app)
host, port = conf['server']['host'], int(conf['server']['port'])

web.run_app(app, host=host, port=port)
