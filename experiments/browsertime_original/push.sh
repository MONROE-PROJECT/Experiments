#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CONTAINER=${DIR##*/}
REPO=hub.docker.com
#CONTAINERTAG=docker.monroe-system.eu/monroe/monroe-web/image # Modify to your own dockerhub user/repo
CONTAINERTAG=mraj/browsertime_original

#docker login ${REPO} && docker tag ${CONTAINER} ${CONTAINERTAG} && docker push ${CONTAINERTAG} && echo "Finished uploading ${CONTAINERTAG}"
docker login  && docker tag ${CONTAINER} ${CONTAINERTAG} && docker push ${CONTAINERTAG} && echo "Finished uploading ${CONTAINERTAG}"



