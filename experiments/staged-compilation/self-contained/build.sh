#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CONTAINER=mptcp

docker pull $(awk '/FROM/{ print $2 }' Dockerfile | head -n1)
docker build --rm --no-cache -t ${CONTAINER} . && echo "Finished building ${CONTAINER}"
