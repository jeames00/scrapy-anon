import logging

from sqlalchemy.orm import load_only
from sqlalchemy.sql import func

from scrapyanon.db.crud import get_random_id
from scrapyanon.db.crud import upsert
from scrapyanon.db.crud import session_scope as db_session
from scrapyanon.db.models import Base, ClientHello, Proxy, ClientHelloProxy

class DatabaseController:

    def get_client_hello(self, type = "random", **kwargs):
        with db_session() as s:
            try:
                platform = kwargs['platform']
                browser = kwargs['browser']
                ch = s.query(ClientHello).\
                    options(load_only('client_hello')).\
                    filter(
                            ClientHello.platform == platform,
                            ClientHello.browser == browser
                    )[6].client_hello
            except:
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
                else:
                    raise Exception

            return ch

    def upsert_tor_nodes(self, tor_nodes):
        with db_session() as s:
            upsert_rows = []
            for x in tor_nodes:
                proxy_model = {
                    'ip_address': x[0],
                    'tor_fingerprint': x[1],
                    'tor_nickname': x[2],
                    'source': 'tor'
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

    def upsert_rows(self, rows, table_name, constraint=None, foreign_keys=None):
        try:
            eval(table_name)
        except NameError:
            logging.debug("DatabaseController: upsert_rows: no table object was found for the name \"{}\"".format(table_name))
            return

        try:
            assert isinstance(rows, list)
        except AssertionError:
            logging.debug("DatabaseController: upsert_rows: an aggregate of rows should be of type list, received {} instead".format(type(rows)))
            return

        with db_session() as s:

            def get_parent_id(parent_attrs):
                table_name = parent_attrs['parent_table']
                column_name = parent_attrs['parent_column']
                val_to_match = parent_attrs['column_value']
                logging.debug("Searching {}.{} for value {}".format(table_name,column_name,val_to_match))
                try:
                    return (lambda a: a.id if a else None)\
                        (s.query(eval(table_name)).\
                        filter(getattr(eval(table_name),column_name) == val_to_match).\
                        first())

                except Exception as e:
                    logging.debug("DatabaseController: update_rows: error searching for foreign_key value {}: {}".format(val_to_match), e)
                    return None


            def is_valid_row_for_upsert(row):
                this_row = row
                for fk in foreign_keys:
                    # is the row a dict?
                    try:
                        assert isinstance(this_row, dict)
                    except AssertionError as e:
                        logging.debug("DabaseController: upsert_rows: each row must be of type dict, received {} instead".format(type(row)))
                        return e
                    parent_id = get_parent_id(fk)


                    #if fk['column_name'] in this_row.keys():
                    #    fk_val = this_row[fk['column_name']]
                    #    fk_id = get_foreign_key_id(
                    #        (fk['table_name'],fk['column_name'],fk_val)
                    #    )
                        # is this fk value in the parent table?
                    if parent_id:
                        this_row[fk['foreign_key']] = parent_id
                    else:
                        return False

                return this_row

            
            # If passed foreign key info, check whether the the fk value(s) has id's in parent table
            if foreign_keys:
                try:
                    assert isinstance(foreign_keys, list)
                except AssertionError as e:
                    logging.debug("DatabaseController: upsert_rows: foreign_keys must be passed as a list of dictionaries, {} passed instead".format(type(foreign_keys)))
                    return e
                upsert_rows = []
                for row in rows:
                    result = is_valid_row_for_upsert(row)
                    # exit if one row is not a dict
                    if isinstance(result, AssertionError):
                        return
                    # not a valid row to upsert if parent table missing this row's fk value
                    elif not result:
                        continue
                    # this row's fk values are all valid
                    elif result:
                        upsert_rows.append(row)
                if len(upsert_rows) == 0:
                    logging.debug("DatabaseController: upsert_rows: no valid rows to upsert")
                    return
                else:
                    rows = upsert_rows
                    

            try:
                upsert(s, eval(table_name), rows, constraint)
            except Exception as e:
                logging.debug("DatabaseController: upsert_rows: upsert error: %s" % str(e))
            s.commit()
