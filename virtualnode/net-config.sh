#!/bin/bash
export PATH=/usr/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Cleanup 
find -L /var/run/netns -type l -delete
rm /var/run/netns/monroe

URL_NOOP=monroe/noop
MNS="ip netns exec monroe"

# Fixing DNS for when running ip exec netns monroe, values taken from
# running docker instance
mkdir  -p /etc/netns/monroe
echo "search lan" > /etc/netns/monroe/resolv.conf
echo "nameserver 8.8.8.8" >> /etc/netns/monroe/resolv.conf
echo "nameserver 8.8.4.4" >> /etc/netns/monroe/resolv.conf

IPDOCKER=$(ip addr show docker0| awk '$1~/^inet$/{print $2}'|awk -F/ '{print $1}')
SUBNETDOCKER=$(ip addr show docker0| awk '$1~/^inet$/{print $2}'| awk -F/ '{print $2}')
NETDOCKER=$(echo $IPDOCKER|awk -F. '{$NF=""; print $0}'|tr ' ' '.')0
MACDOCKER=$(ip link show docker0| awk '$1~/^link\/ether$/{print $2}')

if [ ! -e /var/run/netns/monroe ]; then
  # stop any running containers
  CID=$(docker ps --no-trunc | grep $URL_NOOP | awk '{print $1}' | head -n 1)
  if [ ! -z "$CID" ]; then
    docker stop -t 0 $CID;
  fi

  docker pull $URL_NOOP 2> /dev/null;
  docker run -d --net=bridge $URL_NOOP;
  CID=$(docker ps --no-trunc | grep $URL_NOOP | awk '{print $1}' | head -n 1)
  PID=$(docker inspect -f '{{.State.Pid}}' $CID)
  mkdir -p /var/run/netns;
  rm /var/run/netns/monroe 2>/dev/null || true;
  ln -s /proc/$PID/ns/net /var/run/netns/monroe;

  # rename the docker bridge interface 'eth0' to 'metadata'
  IPMETA=$($MNS ip route | tail -n 1 | awk '{print $NF}')
  $MNS ifconfig eth0 down;
  $MNS ip link set eth0 name metadata;
  $MNS ifconfig metadata $IPMETA up;
  $MNS ip route add default scope global nexthop via $IPDOCKER dev metadata
fi


IPMETA=$($MNS ip route | tail -n 1 | awk '{print $NF}')
ip=$(echo $IPMETA|awk -F. '{print $NF}')
((ip++))
INTERFACES="op0 op1 op2 wlan0 eth0";
for IF in $INTERFACES; do
  IPADRESS=$(echo $IPMETA|awk -F. '{$NF=""; print $0}'|tr ' ' '.')$ip
  SUBNET=$SUBNETDOCKER
  TABLE=$IF.table
  MARK=$(($ip+1000))
  echo "Add veth host.$IF -> $IF"
  ip link add host.$IF type veth peer name montmp

  echo "Up interface host.$IF"
  ip link set host.$IF up

  echo "Adding host.$IF to bridge docker0"
  ip link set host.$IF master docker0

  echo "Move $IF into monroe namespace"
  ip link set montmp netns monroe
  $MNS ip link set dev montmp name $IF

  echo "Up interface $IF (monroe) "
  $MNS ip link set $IF up

  echo "Setting $IPADRESS -> $IF (monroe)"
  $MNS ip addr add $IPADRESS/$SUBNET dev $IF

  echo "Setting up routing tables for $IF (monroe)"
  #echo "$MARK $TABLE" >> /etc/iproute2/rt_tables
  $MNS ip rule add from $IPADRESS table $MARK
  $MNS ip rule add dev $IF table $MARK
  $MNS ip rule add dev lo table $MARK

  #Not working
  #$MSN ip rule add fwmark $MARK table $TABLE
  #$MNS iptables -A PREROUTING -j CONNMARK --restore-mark
  #$MNS iptables -A PREROUTING --match mark --mark $MARK -j ACCEPT
  #$MNS iptables -A PREROUTING -i $IF -j MARK --set-mark $MARK
  #$MNS iptables -A PREROUTING -j CONNMARK --save-mark


  $MNS ip route add $NETDOCKER/$SUBNETDOCKER dev $IF scope link table $MARK
  $MNS ip route add default via $IPDOCKER table $MARK

  # Prepopulate arp
  $MNS ip neighbor add $IPDOCKER lladdr $MACDOCKER dev $IF
  ((ip++))
done
