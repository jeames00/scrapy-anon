from subprocess import Popen, PIPE, STDOUT
import os, socket

passwd = os.environ["POSTGRES_PASSWORD"]

db_host = socket.gethostbyname('database')
db_port = os.environ["DATABASE_PORT"]

DATABASE_URI =\
'postgres+psycopg2://postgres:' + passwd + '@'+db_host+':'+db_port+'/scrapyanon'
