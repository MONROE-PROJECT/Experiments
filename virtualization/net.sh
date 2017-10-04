#!/bin/bash
#MNS=ip netns exec monroe
MNS=""

VTAPPREFIX=macvtap
declare -a IP
declare -a NAME
# We make the disk_image 500 MB larger than necessary
# Will be allocated on demand
disk_size="+500M"
filesystem_image="image.tar"
disk_image="image.qcow2"

# Enumerate the interfaces and create the vtap interfaces
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
sh \"/usr/bin/sed -i -e 's/##GW##/${GW}/g' /etc/network/interfaces.d/${IFNAME}\""
  ip link del ${VTAPNAME}
  i=$((i + 1))
done
GUESTFISHCMD="add ${disk_image}
run
mount /dev/sda1 /
sh \"/usr/sbin/update-initramfs -u\"
sh \"/usr/sbin/grub-install --recheck --no-floppy /dev/sda\"
sh \"/usr/sbin/grub-mkconfig -o /boot/grub/grub.cfg\"
${GUESTFISHDEV}"

#guestfish -x "$GUESTFISHCMD"

#kvm -curses -m 1048 -hda image.qcow2 ${KVMDEV}
