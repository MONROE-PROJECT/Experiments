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

IFINFO=$(python ./interface_information.py $IF)

echo ${IFINFO}

fping -I $IF -D -p 1000 -l 8.8.8.8 | python ./fping_json_formatter.py "${IFINFO}"
