from sql import models, schemas
from sqlalchemy.orm import Session


def get_proxies(db: Session, skip: int = 0, limit: int = 10) -> list[models.Proxy]:
    return db.query(models.Proxy).offset(skip).limit(limit).all()


def get_proxy_by_subdomain_proto(db: Session, sub_domain: str, proto: schemas.Protocol) -> models.Proxy:
    return db.query(models.Proxy).filter(
        models.Proxy.sub_domain == sub_domain,
        models.Proxy.protocol == proto,
    ).first()


def get_proxies_by_deviceid(db: Session, device_id: int, skip: int = 0, limit: int = 10):
    return db.query(models.Proxy).filter(models.Proxy.device_id == device_id).offset(skip).limit(limit).all()


def create_proxy(db: Session, proxy_base: schemas.ProxyBase) -> models.Proxy:
    proxy = models.Proxy(**proxy_base.dict())
    db.add(proxy)
    db.commit()
    db.refresh(proxy)
    return proxy


def delete_proxy(db: Session, proxy_id: int):
    db.query(models.Proxy).filter(models.Proxy.id == proxy_id).delete()
    db.commit()


def get_devices(db: Session, skip: int = 0, limit: int = 10) -> list[models.Device]:
    return db.query(models.Device).offset(skip).limit(limit).all()


def get_devices_by_id(db: Session, ids: list[int]) -> list[models.Device]:
    return db.query(models.Device).filter(models.Device.id.in_(ids)).all()


def get_device_by_id(db: Session, did: int) -> list[models.Device]:
    return db.query(models.Device).filter(models.Device.id == did).first()


def get_device_by_type_address(
        db: Session, device_type: schemas.DeviceType, device_address: str
) -> list[models.Device]:
    return db.query(models.Device).filter(
        models.Device.type == device_type,
        models.Device.address == device_address
    ).first()


def create_device(db: Session, device_create: schemas.DeviceCreate) -> models.Device:
    device = models.Device(**device_create.dict())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def delete_device(db: Session, device_id: int):
    db.query(models.Device).filter(models.Device.id == device_id).delete()
    db.commit()
