#/bin/sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CONTAINER=mptcp

CONTAINERTAG=monroe/${CONTAINER}

docker login && docker tag ${CONTAINER} ${CONTAINERTAG} && docker push ${CONTAINERTAG} && echo "Finished uploading ${CONTAINERTAG}"
