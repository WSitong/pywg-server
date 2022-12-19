from fastapi import APIRouter, Depends, HTTPException
from sql import models, schemas, crud
from sqlalchemy.orm import Session
from sql.database import get_db
from install import get_installed_conf
from IPy import IP
from utils import generate_keys_async, create_peer_async, WGError, save_vpn_files

conf = get_installed_conf()

router = APIRouter(prefix='/api/v1')


@router.get('/proxies', response_model=list[schemas.ProxyDevice])
async def get_proxies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    proxy_models: list[models.Proxy] = crud.get_proxies(db, skip, limit)
    device_models: list[models.Device] = crud.get_devices_by_id(db, [proxy.device_id for proxy in proxy_models])

    proxies: list[schemas.Proxy] = [schemas.Proxy.from_orm(proxy) for proxy in proxy_models]
    devices: list[schemas.Device] = [schemas.Device.from_orm(device) for device in device_models]
    proxy_devices: list[schemas.ProxyDevice] = []
    for proxy in proxies:
        device_bind = None
        for device in devices:
            if device.id == proxy.device_id:
                device_bind = device
                break
        assert device_bind is not None
        proxy_devices.append(schemas.ProxyDevice(
            device=device_bind,
            **proxy.dict()
        ))
    return proxy_devices


@router.post('/proxies', response_model=schemas.ProxyDevice)
async def create_proxy(proxy_base: schemas.ProxyBase, db: Session = Depends(get_db)):
    device = crud.get_device_by_id(db, proxy_base.device_id)
    if device is None:
        raise HTTPException(status_code=400, detail="绑定的设备不存在")

    proxy_model = crud.get_proxy_by_subdomain_proto(db, proxy_base.sub_domain, proxy_base.protocol)
    if proxy_model is not None:
        raise HTTPException(status_code=400, detail="同一个子域名同种协议只能绑定一个设备")

    if not (0 < proxy_base.port < 65536):
        raise HTTPException(status_code=400, detail="端口必须介于1到65535之间")

    proxy_model = crud.create_proxy(db, proxy_base)
    device_model = crud.get_device_by_id(db, proxy_model.device_id)
    proxy = schemas.Proxy.from_orm(proxy_model)
    device = schemas.Device.from_orm(device_model)
    return schemas.ProxyDevice(
        device=device,
        **proxy.dict()
    )


@router.delete('/proxies/{proxy_id}', status_code=204)
async def delete_proxy(proxy_id: int, db: Session = Depends(get_db)):
    return crud.delete_proxy(db, proxy_id)


@router.get('/devices', response_model=list[schemas.Device])
async def get_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_devices(db, skip, limit)


@router.post('/devices', response_model=schemas.Device)
async def create_devices(device_base: schemas.DeviceBase, db: Session = Depends(get_db)):
    private_key, public_key = '', ''
    subnet = IP(conf.vpn.subnet)

    try:
        address = IP(device_base.address)
    except ValueError:
        raise HTTPException(status_code=400, detail="地址不合法")
    if int(device_base.address.split('.')[-1]) == 0:
        raise HTTPException(status_code=400, detail="地址不合法，最后一位不能是0")
    if '/' in device_base.address:
        raise HTTPException(status_code=400, detail="地址不合法，不能包含/")

    device = crud.get_device_by_type_address(db, device_base.type, device_base.address)
    if device is not None:
        raise HTTPException(status_code=400, detail="该设备已存在")

    if device_base.type == schemas.DeviceType.VPN:
        server_address = IP(conf.vpn.address)
        dns_address = IP(conf.vpn.dns)
        if address == server_address:
            raise HTTPException(status_code=400, detail="不能与服务器地址相同")
        if address == dns_address:
            raise HTTPException(status_code=400, detail="不能与DNS地址相同")
        if address not in subnet:
            raise HTTPException(status_code=400, detail=f"地址必须在子网（{subnet}）内")
        try:
            private_key, public_key = await generate_keys_async()
            await create_peer_async(public_key, device_base.address)
        except WGError as error:
            raise HTTPException(status_code=400, detail=str(error))
    else:
        if address in subnet:
            raise HTTPException(status_code=400, detail=f"普通设备的地址不能属于VPN网段")

    device_create = schemas.DeviceCreate(
        private_key=private_key,
        public_key=public_key,
        **device_base.dict()
    )
    device_model = crud.create_device(db, device_create)
    await save_vpn_files(device_model)
    return device_model


@router.delete('/devices/{device_id}', status_code=204)
async def delete_devices(device_id: int, db: Session = Depends(get_db)):
    device = crud.get_device_by_id(db, device_id)
    if device is None:
        raise HTTPException(status_code=400, detail="设备不存在")
    proxies = crud.get_proxies_by_deviceid(db, device_id, 0, 1)
    if len(proxies) > 0:
        raise HTTPException(status_code=400, detail="设备在使用中")
    crud.delete_device(db, device_id)
