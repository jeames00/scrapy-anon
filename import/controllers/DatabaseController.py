import logging

from sqlalchemy.orm import load_only
from sqlalchemy.sql import func

from scrapyanon.db.crud import get_random_id
from scrapyanon.db.crud import upsert
from scrapyanon.db.crud import session_scope as db_session
from scrapyanon.db.models import Base, ClientHello, Proxy, ClientHelloProxy

class DatabaseController:

    def get_client_hello(self, type = "random"):
        with db_session() as s:
            if type == "random": 
                _id = get_random_id(s, ClientHello)

                ch = s.query(ClientHello).\
                    options(load_only('client_hello')).\
                    filter(ClientHello.id == _id).\
                    first().client_hello
            elif type == "tor":
                ch = s.query(ClientHello).\
                    options(load_only('client_hello')).\
                    filter(ClientHello.platform == "tor").\
                    first().client_hello

            return ch

    def upsert_tor_nodes(self, tor_nodes):
        with db_session() as s:
            upsert_rows = []
            for x in tor_nodes:
                proxy_model = {
                    'ip_address': x[0],
                    'tor_fingerprint': x[1],
                    'tor_nickname': x[2],
                    'is_tor_exit_node': True
                }

                upsert_rows.append(proxy_model)

            constraint = 'ip_address_constraint'
            upsert(s, Proxy, upsert_rows, constraint)
            s.commit()

    def update_proxy_blocked_status(self, ip_address, ip_blocked, client_hello, website):
        with db_session() as s:

            client_hello_id = (lambda a: a.id if a else None)\
                (s.query(ClientHello).\
                filter(ClientHello.client_hello == client_hello).\
                first())

            proxy_id = (lambda a: a.id if a else None)\
                (s.query(Proxy).\
                filter(Proxy.ip_address == ip_address).\
                first())

            if not proxy_id or not client_hello_id:
                return

            upsert_rows = []
            model = {
                'client_hello_id': client_hello_id,
                'proxy_id': proxy_id,
                'website': website,
                'blocked': ip_blocked
            }

            upsert_rows.append(model)

            constraint = 'website_proxy_constraint'
            upsert(s, ClientHelloProxy, upsert_rows, constraint)
            s.commit()
