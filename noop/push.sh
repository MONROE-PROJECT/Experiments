#/bin/sh

CONTAINER=noop

REPO=monroe1.cs.kau.se:5000
DOCKERFILE=${CONTAINER}.docker
CONTAINERTAG=${REPO}/monroe/${CONTAINER}

docker login ${REPO} && docker build --rm=true -f ${DOCKERFILE} -t ${CONTAINER} . && docker tag ${CONTAINER} ${CONTAINERTAG} && docker push ${CONTAINERTAG} && echo "Finished uploading ${CONTAINERTAG}"
