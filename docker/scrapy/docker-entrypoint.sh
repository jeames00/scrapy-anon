#!/bin/bash

set -e

source /home/scrapy/.profile

# Scrapyd config port should match nominated custom port number (and bind listening address to '0.0.0.0'
pip_env=`pipenv --venv`
py_ver=`ls $pip_env/lib`
cd $pip_env/lib/$py_ver/site-packages/scrapyd/
echo $SCRAPYD_PORT | xargs -I '{}' sed '/poll_interval/ {s/5.0/1.0/;n; /bind_address/ {s/127.0.0.1/0.0.0.0/;n; /http_port/ {s/6800/{}/}}}' default_scrapyd.conf | sponge default_scrapyd.conf

# Create the scrapy project directory within the bind mount if it doesn't already exist
# Modify settings file to include scrapy-anon modules and cfg file to match custom scrapyd port
# Symlink scrapy-anon modules
if [[ $DEVELOPMENT && ! -d /src/$SCRAPY_PROJECT ]]; then
	cd /src && pipenv run scrapy startproject $SCRAPY_PROJECT
	cd $SCRAPY_PROJECT
	sed -f /sedscript $SCRAPY_PROJECT/settings.py | sponge $SCRAPY_PROJECT/settings.py conv=notrunc
	echo -n $SCRAPYD_PORT | xargs -I '{}' sed '/#url/{s/^#//; /localhost:6800/ {s/6800/{}/;}}' scrapy.cfg | sponge scrapy.cfg
	ln -s ../scrapy-anon/scrapy ScrapyAnon
	ln -s ../../../scrapy-anon/scrapy/spider_stub.py $SCRAPY_PROJECT/spiders
fi

cd /db
# Try to upgrade db with latest version
# If this fails it's becase there's no previous version in db to upgrade
if [[ ! `pipenv run alembic upgrade head` ]]; then
	echo "alembic upgrade head failed, stamping database with HEAD..."
	# Stamp db with latest version (i.e. to make a previous version)
	pipenv run alembic stamp head
	# Generate a new version (schema probably identical to previous)
	pipenv run alembic revision --autogenerate -m "initial setup"
	# Upgrade version in db
	pipenv run alembic upgrade head
fi


# Upsert client-hellos into database
cd /client-hellos && pipenv run python upload-client-hellos.py

cd

memcached &
sleep 5 && deploy &
pipenv run scrapyd

exec "$@"
