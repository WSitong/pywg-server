import os.path
from typing import Optional
from pydantic import BaseModel
import yaml
from pickle import load, PickleError
import shutil


class Website(BaseModel):
    domain: str
    sub_domain: str


class Admin(BaseModel):
    name: str
    password: str


class VPN(BaseModel):
    name: str
    address: str
    dns: str
    listen_port: int
    subnet: str
    private_key: Optional[str] = None
    public_key: Optional[str] = None


class Config(BaseModel):
    website: Website
    admin: Admin
    vpn: VPN


def load_install_conf() -> Config:
    with open(os.path.join('install', 'install.yaml')) as file:
        conf_dict = yaml.load(file, Loader=yaml.Loader)
        return Config(**conf_dict)


__conf: Optional[Config] = None


def get_installed_conf() -> Config:
    global __conf
    if __conf is None:
        file_path = os.path.join('install', 'installed')
        if not os.path.isfile(file_path):
            raise IOError('installed文件不存在，请先运行：python -m install')
        try:
            with open(file_path, 'rb') as file:
                __conf = load(file)
        except PickleError:
            raise IOError('installed文件已损坏，请重新运行：python -m install')
    return __conf


def write_conf(conf: Config, path: str = 'install'):
    data = conf.dict()
    path = os.path.join(path, 'install.yaml')
    with open(path, 'w') as file:
        yaml.dump(data, file)
