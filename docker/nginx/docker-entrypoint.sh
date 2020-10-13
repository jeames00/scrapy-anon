#!/usr/bin/env sh
set -eu

sh -c "echo -n 'scrapyd:' > /etc/nginx/scrapyd_pwd"
sh -c "echo `cat /secrets/SCRAPYD_PASSWORD` | xargs openssl passwd -apr1 >> /etc/nginx/scrapyd_pwd"

envsubst '${SCRAPYD_PORT}' < /etc/nginx/conf.d/scrapyd.conf.template > /etc/nginx/conf.d/scrapyd.conf

exec "$@"
