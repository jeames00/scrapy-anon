#!/bin/sh

if [ -d "/secrets" ]; then
	FILES=/secrets/*
	for f in $FILES
	do
		file="$(basename $f)"
		export $file=`cat $f`
	done

	if [[ `which tor` ]]; then
		export HASHED_TOR_CONTROL_PASSWORD=`tor --hash-password $TOR_CONTROL_PASSWORD`
	fi

fi

