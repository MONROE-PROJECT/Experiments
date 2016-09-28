#/bin/sh

docker pull debian:jessie
docker build --rm=true -f monroe_base.docker -t base . && docker tag base monroe/base 
