nginx
wg-quick up wg-proxy
uvicorn main:app --host 127.0.0.1 --port 8000