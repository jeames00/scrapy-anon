from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, UniqueConstraint,\
ForeignKey, PrimaryKeyConstraint, Boolean
from sqlalchemy.sql import func
from datetime import datetime
from sqlalchemy.orm import relationship
 
Base = declarative_base()

def date_today():
    return datetime.today()

class ClientHello(Base):
    __tablename__ = 'client_hello'
    id = Column(Integer, primary_key=True)
    platform = Column(String, nullable=False)
    browser = Column(String, nullable=False)
    source = Column(String, nullable=False)
    client_hello = Column(String, nullable=False, unique=True)
    updated = Column(Date, default=date_today, nullable=False)

    __table_args__ = (UniqueConstraint(
            'client_hello', 
            name='client_hello_constraint'), {})

    # relationship to child
    client_hello_proxy = relationship(
            "ClientHelloProxy",
            back_populates="client_hello",
            cascade="all, delete, delete-orphan")

class Proxy(Base):
    __tablename__ = 'proxy'
    id = Column(Integer, primary_key=True)
    ip_address = Column(String, nullable=False)
    tor_fingerprint = Column(String, nullable=True, unique=True)
    tor_nickname = Column(String, nullable=True)
    is_tor_exit_node = Column(Boolean, nullable=False)

    __table_args__ = (UniqueConstraint(
        'ip_address',
        name='ip_address_constraint'), {})

    # relationship to child
    client_hello_proxy = relationship(
            "ClientHelloProxy",
            back_populates="proxy",
            cascade="all, delete, delete-orphan")

class ClientHelloProxy(Base):
    __tablename__ = 'client_hello_proxy'
    id = Column(Integer, primary_key=True)
    client_hello_id = Column(Integer, ForeignKey('client_hello.id'), nullable=False)
    proxy_id = Column(Integer, ForeignKey('proxy.id'), nullable=False)
    website = Column(String, nullable=False)
    blocked = Column(Boolean, nullable=False)
    updated = Column(Date, default=date_today)

    __table_args__ = (UniqueConstraint(
        'website', 'proxy_id', name='website_proxy_constraint'), {})

    # relationship to parents
    client_hello = relationship(
            "ClientHello",
            back_populates="client_hello_proxy")
    proxy = relationship(
            "Proxy",
            back_populates="client_hello_proxy")                    
