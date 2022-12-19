import os.path
from install import load_install_conf, write_conf
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

    # # 写入sysctl.conf
    # with open('/etc/sysctl.conf', 'w') as save_file:
    #     save_file.write(f'net.ipv4.ip_forward = 1\n')

    # 写入nginx.conf
    domain = conf.website.domain
    sub_domain = conf.website.sub_domain
    nginx_conf_file_path = os.path.join('/etc/nginx/conf.d', f'{sub_domain}.{domain}.conf')
    with open(nginx_conf_file_path, 'w') as save_file:
        save_file.write('server {\n')
        save_file.write('  listen 80;\n')
        save_file.write('  server_name %s.%s;\n' % (sub_domain, domain))
        save_file.write('  location / {\n')
        save_file.write('    root /app/web;\n')
        save_file.write('    index index.html index.htm;\n')
        save_file.write('  }\n')
        save_file.write('  location /openapi.json {\n')
        save_file.write('    proxy_pass http://127.0.0.1:8000;\n')
        save_file.write('  }\n')
        save_file.write('  location /docs {\n')
        save_file.write('    proxy_pass http://127.0.0.1:8000;\n')
        save_file.write('  }\n')
        save_file.write('  location /api {\n')
        save_file.write('    proxy_pass http://127.0.0.1:8000;\n')
        save_file.write('  }\n')
        save_file.write('}\n')

    # 写入vpn conf
    wg_conf_file_path = os.path.join(f'/etc/wireguard/{conf.vpn.name}.conf')
    with open(wg_conf_file_path, 'w') as save_file:
        save_file.write(f'[Interface]\n')
        save_file.write(f'Address = {conf.vpn.address}/32\n')
        save_file.write(f'ListenPort = {conf.vpn.listen_port}\n')
        save_file.write(f'PrivateKey = {conf.vpn.private_key}\n')
        # save_file.write(f'PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE\n')
        # save_file.write(f'PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE\n')

    # 重写和备份install.yaml到data
    write_conf(conf)

    # 写入installed文件
    with open(os.path.join('install', 'installed'), 'wb') as file:
        dump(conf, file)

    # 写入start.sh
    with open('start.sh', 'w') as save_file:
        save_file.write(f'nginx\n')
        save_file.write(f'wg-quick up {conf.vpn.name}\n')
        save_file.write(f'uvicorn main:app --host 127.0.0.1 --port 8000\n')


asyncio.run(main())
