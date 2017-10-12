#!/bin/bash
#set -x
#MNS=ip netns exec monroe
MNS=""
BASEDIR="."
SCHEDID="test"

VTAPPREFIX=macvtap
declare -a IP
declare -a NAME
# We make the disk_image 500 MB larger than necessary
# Will be allocated on demand
disk_size="+500M"
filesystem_image="image.tar"
disk_image="image.qcow2"

# Enumerate the interfaces and:
# 1. Create the vtap interfaces
# 2. Create the kvm cmd line to connect to said interfaces
# 3. Create the guestfish cmd line to modify the vm to reflect the interfaces
i=0
KVMDEV=""
GUESTFISHDEV=""
for IFNAME in $($MNS basename -a /sys/class/net/*); do
  if [[ ${IFNAME} == "lo" ]]; then
    continue
  fi
  VTAPNAME=${VTAPPREFIX}$i

  echo "Doing ${IFNAME} -> ${VTAPNAME}"
  $MNS ip link add link ${IFNAME} name ${VTAPNAME} type macvtap mode bridge
  sleep 2
  $MNS ip link set dev ${VTAPNAME} up

  IFIP=$($MNS ip -f inet addr show ${IFNAME} | grep -Po 'inet \K[\d.]+')
  VTAPID=$($MNS cat /sys/class/net/${VTAPNAME}/ifindex)

  IP="${IFIP%.*}.3"
  NM="255.255.255.0"
  GW="${IFIP%.*}.1"
  MAC=$($MNS cat /sys/class/net/${VTAPNAME}/address)
  NAME=${IFNAME}
  exec {FD}<>/dev/tap${VTAPID}

  KVMDEV="$KVMDEV \
          -device virtio-net-pci,netdev=net$i,mac=${MAC} \
          -netdev tap,id=net$i,fd=${FD}"
  GUESTFISHDEV="$GUESTFISHDEV
sh \"/usr/bin/sed -e 's/##NAME##/${NAME}/g' /etc/network/netdev-template > /etc/network/interfaces.d/${IFNAME}\"
sh \"/usr/bin/sed -i -e 's/##IP##/${IP}/g' /etc/network/interfaces.d/${IFNAME}\"
sh \"/usr/bin/sed -i -e 's/##NM##/${NM}/g' /etc/network/interfaces.d/${IFNAME}\"
sh \"/usr/bin/sed -i -e 's/##GW##/${GW}/g' /etc/network/interfaces.d/${IFNAME}\"
sh \"/usr/bin/sed -e 's/##MAC##/${MAC}/g' -e 's/##NAME##/${NAME}/g' /etc/network/persistent-net.rules-template >> /etc/udev/rules.d/70-persistent-net.rules\""
  #ip link del ${VTAPNAME}
  i=$((i + 1))
done

# TODO : Fix the mount points
# Add the mounts, these must correspond betwen vm and kvm cmd line
# KVMDEV="$KVMDEV \
#         -fsdevice local,security_model=mapped,id=results,path=$BASEDIR/$SCHEDID \
#         -device virtio-9p-pci,fsdev=results,mount_tag=results"
# KVMDEV="$KVMDEV \
#         -fsdevice local,security_model=mapped,id=outdir,path=$BASEDIR/$SCHEDID \
#         -device virtio-9p-pci,fsdev=outdir,mount_tag=outdir"
# KVMDEV="$KVMDEV \
#         -fsdevice local,security_model=mapped,id=config,path=$BASEDIR/$SCHEDID.conf,readonly \
#         -device virtio-9p-pci,fsdev=config,mount_tag=config"
# KVMDEV="$KVMDEV \
#         -fsdevice local,security_model=mapped,id=nodeid,path=/etc/nodeid,readonly \
#         -device virtio-9p-pci,fsdev=nodeid,mount_tag=nodeid"
#GUESTFISHDEV="$GUESTFISHDEV
#sh \"/usr/bin/sed -e 's/##NAME##/${NAME}/g' /etc/network/netdev-template > /etc/network/interfaces.d/${IFNAME}\""
#mount -t 9p -o trans=virtio test_mount /tmp/shared/ -oversion=9p2000.L,posixacl,cache=loose


# Modify the vm image to reflect the current interface setup
guestfish -x <<-EOF
add ${disk_image}
run
mount /dev/sda1 /
sh "/usr/sbin/update-initramfs -u"
sh "/usr/sbin/grub-install --recheck --no-floppy /dev/sda"
sh "/usr/sbin/grub-mkconfig -o /boot/grub/grub.cfg"
${GUESTFISHDEV}
EOF
echo ${KVMDEV}
sleep 5
kvm -curses -m 1048 -hda image.qcow2 ${KVMDEV}
