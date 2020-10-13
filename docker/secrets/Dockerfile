FROM alpine
RUN apk add --upgrade pwgen bash
COPY ./docker/secrets/docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
