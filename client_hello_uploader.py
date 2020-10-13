#from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from db_config import DATABASE_URI
from models import Base, ClientHello
from crud import session_scope as db_session
from crud import upsert
import sys
import os

engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

with db_session() as s:
    upsert_rows = [] 
    for root, dirs, files in os.walk(os.getcwd()+"/client-hellos"):
        for file in files:
            try:
                with open(root + "/" + file, 'r') as f:
                    data = f.read().replace('\n','')
            except:
                print("unable to open file: " + file)
                sys.exit()
                
            platform = os.path.split(root)[1]
            browser = os.path.split(os.path.split(root)[0])[1]
            source = os.path.split(os.path.split(os.path.split(root)[0])[0])[1]

            client_hello_model = {
                    'platform': platform,
                    'browser': browser,
                    'source': source,
                    'client_hello': data
            }

            upsert_rows.append(client_hello_model)

    constraint = 'client_hello_constraint'
    upsert(s, ClientHello, upsert_rows, constraint)
    s.commit()
