#!/bin/sh

cd "$(dirname $0)"

if [ $# -ne 4 ]; then
    echo "Usage: $0 interface max_time (seconds) interval (seconds) segmentsize (B)"
    exit 1
fi

IF=$1
MAX_TIME=$2
INTERVAL=$3
#SEGSIZE=1388
SEGSIZE=$4
SEGMENTS="1 3 8 11 19 32 64 91 128 182 236"
URL="http://speedtest.bahnhof.net/1000M.zip"

python curl_wrapper_shortflows.py --interface ${IF} --time ${MAX_TIME} --url ${URL} --interval ${INTERVAL} --segments ${SEGMENTS} --segmentsize ${SEGSIZE}
