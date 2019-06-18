#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CONTAINER=mptcp-nodetest

echo "Login to docker.cs.kau.se"
docker login docker.cs.kau.se
echo "Pull mptcp container"
docker pull docker.cs.kau.se/monroe/containers/mptcp:build

docker pull $(awk '/FROM/{ print $2 }' Dockerfile | head -n1)
docker build --rm --no-cache -t ${CONTAINER} . && echo "Finished building ${CONTAINER}"
