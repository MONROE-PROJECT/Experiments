#!/bin/bash
export PATH=/usr/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

./build.sh
URL_NOOP=monroe/noop
URL_VIRTUAL=virtualnode

CIDNOOP=$(docker ps --no-trunc | grep $URL_NOOP | awk '{print $1}' | head -n 1)

CID=$(docker ps --no-trunc | grep $URL_VIRTUAL | awk '{print $1}' | head -n 1)
if [ ! -z "$CID" ]; then
  docker stop -t 0 $CID;
fi

docker run -d --net=container:$CIDNOOP virtualnode
