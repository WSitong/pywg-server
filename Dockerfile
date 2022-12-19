FROM winston1995/nginx:1.23-python3.10-slim

EXPOSE 80
EXPOSE 51820/udp

WORKDIR /app
COPY . /app/

RUN apk add --no-cache wireguard-tools \
    && pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ \
    && python -m install

CMD ["sh", "start.sh"]