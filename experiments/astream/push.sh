#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

#CONTAINER=${DIR##*/}
CONTAINER=astream
CONTAINERTAG=cmidoglu/astream-lightweight
#CONTAINERTAG=cmidoglu/astream

#docker login &&
docker tag ${CONTAINER} ${CONTAINERTAG} && docker push ${CONTAINERTAG} && echo "Finished uploading ${CONTAINERTAG}"
