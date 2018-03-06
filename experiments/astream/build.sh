#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

#CONTAINER=${DIR##*/}
CONTAINER=astream
#DOCKERFILE=Dockerfile
DOCKERFILE=${CONTAINER}.docker

NO_CACHE=--no-cache

docker pull monroe/base
docker build $NO_CACHE --rm=true -f ${DOCKERFILE} -t ${CONTAINER} . && echo "Finished building ${CONTAINER}"
