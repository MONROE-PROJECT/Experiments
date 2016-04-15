#!/bin/sh

cd $(dirname $0)

if [ $# -ne 1 ]; then
    echo "Usage: $0 interface"
    exit 1
fi

IF=$1

if [ ! "$(ip a |grep $IF | grep LOWER_UP)" ]; then
  echo "No $IF is configured exits"
  exit 1
fi

# FIXME: Need to check that $IF exists, otherwise
# fping will default to the default route.
# Add this check after interface_to_id check is enabled, wrap fping in conditional wrapper.

fping -I $IF -D -p 1000 -l 8.8.8.8 | python ./fping_json_formatter.py $IF
#fping -I $IF -D -p 1000 -l 8.8.8.8 | python ./fping_json_formatter.py $IFID
