#!/bin/sh
URL_PUBLISHER=metadata-publisher

cd ${URL_PUBLISHER}
./build.sh ${URL_PUBLISHER}
cd ..

#Do the netconfig
scripts/net-config.sh ${URL_PUBLISHER}

echo "To run and test you container do :"
echo "./run-virtualnode.sh <container> <optional docker commandline options>"
echo 'For example : ./run-virtualnode.sh monroe/base "-ti --entrypoint bash"'
