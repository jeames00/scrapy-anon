FROM alpine
RUN apk update && apk add --no-cache pwgen bash
COPY ./docker/secrets/docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
