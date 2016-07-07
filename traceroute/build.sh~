#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CONTAINER=${DIR##*/}
DOCKERFILE=${CONTAINER}.docker

docker build --rm=true -f ${DOCKERFILE} -t ${CONTAINER} . && echo "Finished building ${CONTAINER}"
