FROM nginx:alpine

RUN apk update && apk add openssl

COPY ./docker/nginx/docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

COPY ./docker/nginx/scrapyd.conf.template /etc/nginx/conf.d/scrapyd.conf.template

RUN echo "daemon off;" >> /etc/nginx/nginx.conf
