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
RUN cat /export-secrets.sh >> /home/tor/.bashrc

COPY ./docker/tor/launch-tor.py /home/tor
RUN chmod +x /home/tor/launch-tor.py

USER tor

RUN pipenv install --ignore-pipfile
COPY ./protobuf/launchtor.proto /home/tor
WORKDIR /home/tor
RUN pipenv run python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. ./launchtor.proto
