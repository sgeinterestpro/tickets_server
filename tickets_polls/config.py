"""
filename: config.py
datetime: 2019-04-22
author: muumlover
"""

import pathlib

import yaml
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa


def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = f.read()
        config = yaml.load(cfg, Loader=yaml.BaseLoader)  # 用load方法转字典
    return config


def setup_config(app):
    conf = load_config(str(pathlib.Path('.') / 'config' / 'polls.yaml'))
    app['config'] = conf

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=1024,
        backend=default_backend()
    )
    public_key = private_key.public_key()

    app['private_key'] = private_key
    app['public_key'] = public_key
