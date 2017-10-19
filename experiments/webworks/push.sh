#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CONTAINER=${DIR##*/}
REPO=docker.monroe-system.eu
CONTAINERTAG=docker.monroe-system.eu/monroe/monroe-web/image # Modify to your own dockerhub user/repo

docker login ${REPO} && docker tag ${CONTAINER} ${CONTAINERTAG} && docker push ${CONTAINERTAG} && echo "Finished uploading ${CONTAINERTAG}"
