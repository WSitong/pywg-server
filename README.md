# pywg-server

## 构建和安装
```shell
git clone https://github.com/WSitong/pywg-server.git
cd pywg-server
# 修改website设置
vim install/install.yaml
# 保存install.yaml

docker build -t pywg-server:latest .
docker run -it -p 80:80 -p 51820:51820/udp -v ~/data:/app/data --rm --privileged pywg-server:latest
```