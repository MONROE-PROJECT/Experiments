#!/bin/sh

cd "$(dirname $0)"

if [ $# -ne 4 ]; then
    echo "Usage: $0 interface max_download_size (MB) max_time (seconds) interval (seconds)"
    exit 1
fi

IF=$1
MAX_SIZE=$2
MAX_TIME=$3
INTERVAL=$4
URL="http://speedtest.bahnhof.net/1000M.zip"

python curl_wrapper.py --interface=${IF} --time=${MAX_TIME} --size=${MAX_SIZE} --url=${URL} --interval=${INTERVAL}

#curl -o /dev/null --raw --silent --write-out "{ remote: %{remote_ip}:%{remote_port}, size: %{size_download}, speed: %{speed_download}, time: %{time_total}, time_download: %{time_starttransfer} }" --interface ${IF} --max-time ${MAX_TIME} --range 0-${MAX_SIZE} http://speedtest.bahnhof.net/1000M.zip
