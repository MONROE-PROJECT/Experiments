#!/bin/bash
#set -x
MNS="ip netns exec monroe"
BASEDIR="."
SCHEDID="test"

VTAPPREFIX=macvtap
disk_image="image.qcow2"

# Enumerate the macvtap interfaces and delete them
for IFNAME in $($MNS ls /sys/class/net/|grep ${VTAPPREFIX}); do
  echo "Deleting ($MNS) ${IFNAME}"
  $MNS ip link del ${IFNAME}
done


#Delete the mounts ??? 
declare -A mounts=( [results]=$BASEDIR/$SCHEDID [config-dir]=$BASEDIR/$SCHEDID-conf/ )
for m in "${!mounts[@]}"; do
  p=${mounts[$m]}
  #rm -rf ${p}
  echo "Deleting ${p} (maybe)"
done

#Delete the image
echo "Deleting ${disk_image}"
rm -f ${disk_image}
