#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CONTAINER=${DIR##*/}

docker pull monroe/base:virt
docker build --rm=true --no-cache -t ${CONTAINER} . && echo "Finished building ${CONTAINER}"
