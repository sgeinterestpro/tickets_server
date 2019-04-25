"""
filename: config.py
datetime: 2019-04-22
author: muumlover
"""

import pathlib

import yaml


def load_config(config_path):
    with open(config_path, 'r') as f:
        cfg = f.read()
        config = yaml.load(cfg, Loader=yaml.BaseLoader)  # 用load方法转字典
    return config


def setup_config(app):
    conf = load_config(str(pathlib.Path('.') / 'config' / 'polls.yaml'))
    app['config'] = conf
