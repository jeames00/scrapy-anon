FROM python:3.8-slim-buster
RUN pip install pipenv \
	&& apt update \
	&& apt install -y --no-install-recommends gcc python3-dev libssl-dev git memcached
COPY ./docker/scrapy/Pipfile* /
COPY ./docker/scrapy/sponge /usr/bin/
COPY import /import/scrapyanon/
COPY scrapy /ScrapyAnon
RUN echo PYTHONPATH=/import:/grpcimport > /.env
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

USER scrapy

RUN pipenv install --deploy --ignore-pipfile
RUN pipenv run python -m grpc_tools.protoc -Iimport/scrapyanon/protobuf --python_out=grpcimport --grpc_python_out=grpcimport launchtor.proto
RUN pipenv run python -m grpc_tools.protoc -Iimport/scrapyanon/protobuf --python_out=grpcimport --grpc_python_out=grpcimport http.proto
