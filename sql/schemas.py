from pydantic import BaseModel
import enum


class Protocol(str, enum.Enum):
    HTTP = 'http'
    # HTTPS = 'https'


class DeviceType(enum.IntEnum):
    Normal = 0
    VPN = 1


class DeviceBase(BaseModel):
    address: str
    name: str
    type: DeviceType


class DeviceCreate(DeviceBase):
    private_key: str
    public_key: str


class Device(DeviceBase):
    id: int

    class Config:
        orm_mode = True


class ProxyBase(BaseModel):
    sub_domain: str
    port: int
    device_id: int
    protocol: Protocol


class Proxy(ProxyBase):
    id: int

    class Config:
        orm_mode = True


class ProxyDevice(ProxyBase):
    id: int
    device: Device
