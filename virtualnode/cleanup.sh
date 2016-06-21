#!/bin/bash
export PATH=/usr/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Cleanup 
find -L /var/run/netns -type l -delete
rm /var/run/netns/monroe

URL_NOOP=monroe/noop
URL_VIRTUAL=virtualnode

CID=$(docker ps --no-trunc | grep $URL_NOOP | awk '{print $1}' | head -n 1)
if [ ! -z "$CID" ]; then
  docker stop -t 0 $CID;
fi

CID=$(docker ps --no-trunc | grep $URL_VIRTUAL | awk '{print $1}' | head -n 1)
if [ ! -z "$CID" ]; then
  docker stop -t 0 $CID;
fi
