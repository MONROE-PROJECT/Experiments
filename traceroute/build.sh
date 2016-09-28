#!/bin/bash
docker pull monroe/base

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CONTAINER=${DIR##*/}
DOCKERFILE=${CONTAINER}.docker

docker pull monroe/base
docker build --rm --no-cache -f ${DOCKERFILE} -t ${CONTAINER} . && echo "Finished building ${CONTAINER}"
