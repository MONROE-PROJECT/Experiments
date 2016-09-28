#/bin/sh

docker login && docker push monroe/base && echo "Now rebuild all images that are built on monroe/base"
