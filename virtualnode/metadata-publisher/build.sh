#!/bin/sh
URL_PUBLISHER=$1
docker build --pull=true -t ${URL_PUBLISHER} . && echo "Finished building ${URL_PUBLISHER}"
