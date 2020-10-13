#!/bin/bash

set -e

if [[ ! -f "/secrets/POSTGRES_PASSWORD" ]]; then
	echo `pwgen -Bs1 64` > /secrets/POSTGRES_PASSWORD
fi

if [[ ! -f "/secrets/TOR_CONTROL_PASSWORD" ]]; then
	echo `pwgen -Bs1 64` > /secrets/TOR_CONTROL_PASSWORD
fi

if [[ ! -f "/nginx-secrets/SCRAPYD_PASSWORD" ]]; then
	echo `pwgen -Bs1 64` > /nginx-secrets/SCRAPYD_PASSWORD
fi

exec "$@"
