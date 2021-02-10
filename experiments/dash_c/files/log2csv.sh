#!/usr/bin/env bash

# This script concatenates and converts dashc logs to CSV format.

if [ "$#" -eq 0 ]; then
    echo "Usage: $0 FILE... "
    exit 1
fi 

echo "Id,Seg_#,Arr_time,Del_Time,Stall_Dur,Rep_Level,Del_Rate,Act_Rate,Byte_Size,Buff_Level"

for filename in "$@"
do
    tail -n +2 "$filename"              | \
    sed '/^New connection was opened/d' | \
    sed "s/^  */$filename,/g"           | \
    sed 's/sta\(.*\)\.log/\1/g'         | \
    sed 's/  */,/g'
done
