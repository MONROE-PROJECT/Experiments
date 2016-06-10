#/bin/sh

CONTAINER=template

REPO=monroe1.cs.kau.se:5000
DOCKERFILE=experiment.docker
CONTAINERTAG=${REPO}/monroe/${CONTAINER}

docker login ${REPO} && docker build --rm=true -f ${DOCKERFILE} -t ${CONTAINER} . && docker tag ${CONTAINER} ${CONTAINERTAG} && docker push ${CONTAINERTAG} && echo "Finished uploading ${CONTAINERTAG}"
