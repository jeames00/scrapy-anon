from subprocess import Popen, PIPE, STDOUT
import os, socket

import scrapyanon.secrets as secrets

passwd = secrets.POSTGRES_PASSWORD
#db_host = socket.gethostbyname('database')
db_port = os.environ["DATABASE_PORT"]

DATABASE_URI =\
'postgres+psycopg2://postgres:' + passwd + '@database:'+db_port+'/scrapyanon'
