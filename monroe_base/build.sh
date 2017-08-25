#/bin/sh

TMPNAME=monroe-base-local
NAME=monroe/base
TAG=staging

docker pull debian:stretch && docker build --rm --no-cache -f monroe_base.docker -t ${TMPNAME} . \
&& ID=$(docker run -d ${TMPNAME} /bin/bash) \
&& docker export ${ID} | docker import - ${NAME}:${TAG} && docker rm -f ${ID} && docker rmi -f ${TMPNAME} && docker images -a |grep "${NAME} "
