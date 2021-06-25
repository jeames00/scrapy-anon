FROM python:3.8-slim-buster
RUN pip install pipenv \
	&& apt update \
	&& apt install -y --no-install-recommends gcc python3-dev libssl-dev \
	git memcached qt5-default libqt5webkit5-dev build-essential python-lxml \
	python-pip xvfb
COPY ./docker/scrapy/Pipfile* /
COPY ./docker/scrapy/sponge /usr/bin/
COPY scrapy /ScrapyAnon

COPY ./docker/scrapy/upload-client-hellos.py client-hellos /client-hellos/
RUN useradd -m scrapy
#RUN chown -R scrapy:scrapy /import/scrapyanon/db

RUN mkdir /grpcimport
RUN chown -R scrapy:scrapy /grpcimport
#COPY protobuf/*.proto /grpcimport/

#RUN mkdir /grpc

COPY ./docker/scrapy/docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
COPY ./docker/scrapy/sedscript /
COPY ./docker/scrapy/deploy /usr/local/bin/
RUN chmod +x /usr/local/bin/deploy

#USER scrapy

RUN pipenv install --deploy --ignore-pipfile
