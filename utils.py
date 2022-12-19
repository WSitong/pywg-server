import os.path
from pywireguard.factory import Peer
from IPy import IP
import pywireguard.factory as wg
import traceback
import asyncio.subprocess
from asyncio import create_subprocess_exec, sleep
from install import get_installed_conf
from sql import models
import qrcode

__wg_server = None


class WGError(Exception):
    pass


async def generate_keys_async() -> tuple[str, str]:
    pri_key = await generate_private_key_async()
    pub_key = await generate_public_key_async(pri_key)
    return pri_key, pub_key


async def generate_private_key_async() -> str:
    try:
        p = await create_subprocess_exec('wg', 'genkey',
                                         stdout=asyncio.subprocess.PIPE,
                                         stderr=asyncio.subprocess.PIPE)
        out, err = await p.communicate()
        assert err == b''
        return out.decode().strip()
    except Exception:
        traceback.print_exc()
        raise WGError('无法创建私钥')


async def generate_public_key_async(pri_key: str) -> str:
    try:
        p = await create_subprocess_exec('wg', 'pubkey',
                                         stdin=asyncio.subprocess.PIPE,
                                         stdout=asyncio.subprocess.PIPE,
                                         stderr=asyncio.subprocess.PIPE)
        out, err = await p.communicate(input=pri_key.encode())
        assert err == b''
        return out.decode().strip()
    except Exception:
        traceback.print_exc()
        raise WGError('无法创建公钥')


async def create_wg_server():
    global __wg_server
    if __wg_server is None:
        __wg_server = wg.Interface('wg-proxy')
    return __wg_server


async def create_peer_async(public_key: str, address: str):
    try:
        conf = get_installed_conf()
        ip = IP(address)
        peer = Peer(public_key.encode(), allowed_ips=[f'{ip}/32', conf.vpn.subnet])
        wg_server = await create_wg_server()
        wg_server.upsert_peer(peer)
        p = await create_subprocess_exec('ip', '-4', 'address', 'add', f'{ip}/32', 'dev', 'wg-proxy',
                                         stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
        out, err = await p.communicate()
        if b'File exits' in err:
            err = b''
        assert err == b''
    except Exception:
        traceback.print_exc()
        raise WGError('无法创建设备虚拟专用隧道')


async def save_vpn_files(device: models.Device):
    directory = 'web/vpn'
    if not os.path.isdir(directory):
        os.mkdir(directory)
    directory = os.path.join(directory, str(device.id))
    if not os.path.isdir(directory):
        os.mkdir(directory)

    website = get_installed_conf().website
    vpn_conf = get_installed_conf().vpn

    lines = [
        f'[Interface]',
        f'PrivateKey = {device.private_key}',
        f'Address = {device.address}/32',
        f'DNS = {vpn_conf.dns}',
        f'',
        f'[Peer]',
        f'PublicKey = {vpn_conf.public_key}',
        f'AllowedIPs = {vpn_conf.address}/32, {vpn_conf.subnet}',
        f'EndPoint = {website.sub_domain}.{website.domain}:{vpn_conf.listen_port}',
    ]

    with open(os.path.join(directory, f'{device.name}.conf'), 'w') as conf_file:
        for line in lines:
            conf_file.write(f'{line}\n')
            await sleep(0)

    img = qrcode.make('\n'.join(lines))
    img.save(os.path.join(directory, f'{device.name}.png'))

