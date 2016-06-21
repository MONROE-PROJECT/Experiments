#!/bin/bash
export PATH=/usr/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

CID=$(docker ps --no-trunc | grep virtualnode | awk '{print $1}' | head -n 1)

if [ -z "$CID" ]; then
  ./run-virtualnode.sh
fi

CID=$(docker ps --no-trunc | grep virtualnode | awk '{print $1}' | head -n 1)

docker exec -it $CID bash
