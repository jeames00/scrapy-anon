FROM python:3.8-slim-buster
RUN pip install pipenv \
	&& apt update \
	&& apt install -y --no-install-recommends gcc python3-dev libssl-dev tor

COPY ./docker/tor/docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

COPY ./docker/tor/Pipfile* /
COPY ./docker/export-secrets.sh /

RUN useradd -m tor
RUN cat /export-secrets.sh >> /home/tor/.profile

COPY import /import/scrapyanon/

RUN mkdir /grpcimport
RUN chown -R tor:tor /grpcimport

RUN echo PYTHONPATH=/import:/grpcimport > /.env

COPY ./docker/tor/launch-tor.py /home/tor
RUN chmod +x /home/tor/launch-tor.py

# Allow basic Tor connections on port 9050
RUN echo SocksPort 0.0.0.0:9050 >> /etc/tor/torrc


USER tor
RUN pipenv install --ignore-pipfile
RUN pipenv run python -m grpc_tools.protoc -Iimport/scrapyanon/protobuf --python_out=grpcimport --grpc_python_out=grpcimport launchtor.proto
