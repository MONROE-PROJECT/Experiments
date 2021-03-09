#/bin/sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CONTAINER=${DIR##*/}
CONTAINERTAG=monroe/${CONTAINER}:5genesis-$(git rev-parse --symbolic-full-name --abbrev-ref HEAD)

docker login && docker tag ${CONTAINER} ${CONTAINERTAG} && docker push ${CONTAINERTAG} && echo "Finished uploading ${CONTAINERTAG}"
