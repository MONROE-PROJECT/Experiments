#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CONTAINER=${DIR##*/}
DOCKERFILE=${CONTAINER}.docker

docker pull debian:jessie
docker build --no-cache --rm -f ${DOCKERFILE} -t ${CONTAINER} . && echo "Finished building ${CONTAINER}"
