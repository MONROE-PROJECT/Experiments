#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CONTAINER=mptcp

#Ouch how ugly
docker pull $(awk '/FROM/{ print $2 }' Dockerfile | head -n1)
docker pull $(awk '/FROM/{ print $2 }' Dockerfile | tail -n1)

docker build --rm --no-cache -t ${CONTAINER} . && echo "Finished building ${CONTAINER}"
