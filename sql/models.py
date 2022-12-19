from sqlalchemy import Column, Integer, String
from .database import Base


class Proxy(Base):
    __tablename__ = 'proxies'

    id = Column(Integer, primary_key=True, index=True)
    sub_domain = Column(String, unique=True)
    port = Column(Integer)
    device_id = Column(Integer)
    protocol = Column(String)


class Device(Base):
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String)
    name = Column(String)
    """
    type: 1 - 内网IP, address必须是127.0.0.1
          2 - 公网IP
          3 - VPN IP, 此时vpn、private_key、public_key才有值
    """
    type = Column(Integer)
    private_key = Column(String)
    public_key = Column(String)
