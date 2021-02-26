#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CONTAINER=${DIR##*/}

docker pull $(awk '/FROM/{ print $2 }' Dockerfile)
docker build --rm --no-cache -t temp . && echo "Finished building temp"
ID=$(docker run -d --entrypoint bash temp)
docker export ${ID} | docker import - test
docker build -t ${CONTAINER} -f Dockerfile-sq .
docker rm -f ${ID}
docker rmi temp
docker rmi test
