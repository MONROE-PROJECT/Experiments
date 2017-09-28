#/bin/sh

NAME=monroe/base
TAG=staging

docker pull monroe/base && docker build --rm --no-cache -f monroe_base-inc.docker -t ${NAME}:${TAG} . \
&& docker images -a |grep "${NAME} "
