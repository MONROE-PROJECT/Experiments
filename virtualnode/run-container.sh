#!/bin/sh
export PATH=/usr/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

#./build.sh
URL_PUBLISHER=metadata-publisher
URL_CONTAINER=$1
DOCKER_OPTS=$2

CIDPUB=$(docker ps --no-trunc | grep ${URL_PUBLISHER} | awk '{print $1}' | head -n 1)
CID=$(docker ps --no-trunc | grep ${URL_CONTAINER} | awk '{print $1}' | head -n 1)
if [ ! -z "${CID}" ]; then
  docker stop -t 0 ${CID}
fi

docker run -v /mnt/hgfs/host/results/:/monroe/results/ --net=container:${CIDPUB} ${DOCKER_OPTS}  ${URL_CONTAINER} 
