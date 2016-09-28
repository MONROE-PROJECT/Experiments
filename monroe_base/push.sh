#/bin/sh

docker login && docker push monroe/base && echo "Now rebuild all images that are built on monroe/base"
#Experimential
#docker login && docker build --rm=true -f monroe_base.docker -t base .
#ID=$(docker run -d base /bin/bash)
#docker export $ID | docker import – monroe/base && docker push monroe/base && echo "Now rebuild all images that are built on monroe/base"
