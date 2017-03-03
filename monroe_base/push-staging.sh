#/bin/sh

docker login && docker push monroe/base:staging && echo "Pushed staging now rebuild all images that are built on monroe/base"
