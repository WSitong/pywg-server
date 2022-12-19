import os.path
from install import load_install_conf
from utils import generate_public_key_async, generate_keys_async
from IPy import IP
from pickle import dump
import asyncio


async def main():
    conf = load_install_conf()

    # 检查website
    assert os.path.isfile(os.path.join('install', conf.website.nginx))
    assert conf.website.domain != ''
    assert conf.website.sub_domain != ''

    # 检查admin
    assert conf.admin.name != ''
    assert conf.admin.password != ''

    # 检查vpn
    assert conf.vpn.name != ''
    assert conf.vpn.address != ''
    assert conf.vpn.dns != ''
    assert conf.vpn.subnet != ''
    address = IP(conf.vpn.address)
    dns = IP(conf.vpn.dns)
    subnet = IP(conf.vpn.subnet)
    assert dns == address
    assert address in subnet
    assert dns in subnet
    assert 3000 < conf.vpn.listen_port < 65536
    if conf.vpn.private_key is None:
        pri_key, pub_key = await generate_keys_async()
        conf.vpn.private_key = pri_key
        conf.vpn.public_key = pub_key
    if conf.vpn.public_key is None:
        conf.vpn.public_key = await generate_public_key_async(conf.vpn.private_key)
    assert await generate_public_key_async(conf.vpn.private_key) == conf.vpn.public_key

    # 写入nginx.conf
    domain = conf.website.domain
    sub_domain = conf.website.sub_domain
    nginx_conf_file_path = os.path.join('/etc/nginx/conf.d', f'{sub_domain}.{domain}.conf')
    with open(nginx_conf_file_path, 'w') as save_file:
        with open(os.path.join('install', conf.website.nginx)) as conf_file:
            content = conf_file.read()
        content = content % (sub_domain, domain)
        save_file.write(content)

    # 写入wg-proxy.conf
    wg_conf_file_path = os.path.join('/etc/wireguard/wg-proxy.conf')
    with open(wg_conf_file_path, 'w') as save_file:
        save_file.write(f'[Interface]\n')
        save_file.write(f'Address = {conf.vpn.address}/32\n')
        save_file.write(f'ListenPort = {conf.vpn.listen_port}\n')
        save_file.write(f'PrivateKey = {conf.vpn.private_key}\n')
        save_file.write(f'PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE\n')
        save_file.write(f'PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE\n')

    # 写入installed文件
    with open(os.path.join('install', 'installed'), 'wb') as file:
        dump(conf, file)


asyncio.run(main())
