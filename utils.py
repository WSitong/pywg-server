from pywireguard.factory import Peer
from IPy import IP
import pywireguard.factory as wg
import traceback
import asyncio.subprocess
from asyncio import create_subprocess_exec
from install import get_installed_conf

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
        # peer = Peer(public_key.encode(), allowed_ips=['0.0.0.0/0'])
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
