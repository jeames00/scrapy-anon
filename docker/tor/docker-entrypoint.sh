#!/bin/bash

set -e

source /home/tor/.profile

tor &
pipenv run python ~/launch-tor.py

exec "$@"
