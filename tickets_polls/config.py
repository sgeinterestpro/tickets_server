"""
filename: config.py
datetime: 2019-04-22
author: muumlover
"""
import base64
import pathlib

import yaml
from aiohttp.abc import Application
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_der_public_key, load_der_private_key


def load_public_key(pem_key):
    b64data = '\n'.join(pem_key.splitlines()[1:-1])
    derdata = base64.b64decode(b64data)
    key = load_der_public_key(derdata, default_backend())
    return key


def load_private_key(pem_key, password=None):
    b64data = '\n'.join(pem_key.splitlines()[1:-1])
    derdata = base64.b64decode(b64data)
    key = load_der_private_key(derdata, password, default_backend())
    return key


def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = f.read()
        config = yaml.load(cfg, Loader=yaml.FullLoader)  # 用load方法转字典
    return config


def setup_config(app: Application) -> None:
    conf = load_config(str(pathlib.Path('.') / 'config' / 'polls.yaml'))
    app['config'] = conf

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=1024,
        backend=default_backend()
    )

    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    print(private_pem.decode())

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    print(public_pem.decode())

    encrypt = public_key.encrypt('text'.encode(), padding.PKCS1v15())
    assert private_key.decrypt(encrypt, padding.PKCS1v15()).decode() == 'text'

    # private_key = load_private_key("""-----BEGIN RSA PRIVATE KEY-----
    # MIICXQIBAAKBgQC3IJ9m6Z/uLfHGsDl3ZsD7na8YHlK8dySw+lZmlDtL4ADOKNSm
    # 95Pl3XIe60S2+m74IjeayfC+FGMaLmkg78EwvB2b+g2q0qFnxy5VlcKJKdu/mmbV
    # bJA3NSMnqkFRUv7zqCpmYoY8Q3STJAGeSQ3mfjHNqtZ3XoOXA970AGBkcwIDAQAB
    # AoGBAKVmkLLKBoqA8uQrXOwsYdehd3lIQiA5WGmE4i7qaZhBbVjHZjKcYPf4CFBG
    # 3RyLm1kAxspG5Os5zLzj+E4oXosXfHLKjcZblskShWBeFS3YQcKZWHfQ/W1+Bc9U
    # Iuu75jA50Su8OHFshEiV1jX21+cvvtD2gLnLFzFkoFzOZZsRAkEA4woWO6FsBtYh
    # 0c6ZXi11Xv3zFh6pQJTPtEkVLPDcXD9cweWRMw0GiV2WphAu0xMYfz7P5aBkvgzx
    # Ctg6ywevewJBAM58mg2iUsv/JrFj0prUo8XiylYoQkYowteHZatXqaHqxbutGibj
    # Tc/lmb4SmV5Hud+7ha+CsuxeZH7a468C0WkCQQDYnmoiENziFPKFnKoGCjdfH8sM
    # AssXvCQEbmpOy6xkM2xL772+yKHA9FNlNDGI4EJSPdrby1HzZqOg5jgKONX7AkAJ
    # VEXdkdTt1JRZ9WmhhzPzD+EWbXE5HERZWou0ZxyJ7UKLzTFeSmzMlNISbWKyiMkU
    # G7PZjy0oUsd1l8wrrxPpAkAYwlK/HMZqd7VRBt/P5uTbVQY09GSZOh6yzoNABhXj
    # 0ywkcHUsPe/FZ3V7y1BbTxLBFamtedQlGq1CJI/q7WLR
    # -----END RSA PRIVATE KEY-----""")

    # public_key = load_public_key("""-----BEGIN PUBLIC KEY-----
    # MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC3IJ9m6Z/uLfHGsDl3ZsD7na8Y
    # HlK8dySw+lZmlDtL4ADOKNSm95Pl3XIe60S2+m74IjeayfC+FGMaLmkg78EwvB2b
    # +g2q0qFnxy5VlcKJKdu/mmbVbJA3NSMnqkFRUv7zqCpmYoY8Q3STJAGeSQ3mfjHN
    # qtZ3XoOXA970AGBkcwIDAQAB
    # -----END PUBLIC KEY-----""")

    app['private_key'] = private_key
    # app['public_key'] = public_key
