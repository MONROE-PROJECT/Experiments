#!/bin/bash

#!/bin/bash
USER="root"
echo "Creating keys"
# probaly fails if not root due to home directory
ssh-keygen -t rsa -b 4096 -f /${USER}/.ssh/id_rsa -P ""
cat /${USER}/.ssh/id_rsa.pub > /${USER}/.ssh/authorized_keys

echo "Starting sshd"
/usr/sbin/sshd


# Figure out ip adresses
BINDIP=""
for INT in eth0 wlan0 op0 op1 op2
do
  [[ -z  ${BINDIP}  ]] && BINDIP=$(ip -f inet addr show ${INT} |grep -Po 'inet \K[\d.]+')
done
[[ -z  ${BINDIP}  ]] && echo "No IP exiting" && exit

# Assumes /24 and gw on .1 Address so alot of assumptions
#GWIP=$(echo ${BINDIP}|awk -F. '{$NF="1"; gsub(" ", ".", $0); print $0 }')

#route del default
#route add default gw ${GWIP}
#echo "Route is changed to IP "${GWIP}

SERVER=$(/usr/bin/python /opt/monroe/client.py ${BINDIP}

#Start tunnel and loop forever
while true
do
echo "To connect:"
echo "#############################"
echo -n "echo \""
cat /${USER}/.ssh/id_rsa
echo "\" > monroe_private_key"
echo "chmod 0600 monroe_private_key"
echo "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i monroe_private_key -p ${PORT} ${USER}@${SSHHOST}"
echo "#############################"
/usr/bin/ssh -b ${BINDIP} -NTC -o ServerAliveInterval=60 -o ExitOnForwardFailure=yes -o StrictHostKeyChecking=no -o  ServerAliveCountMax=3  -o ConnectTimeout=10 -o BatchMode=yes -o UserKnownHostsFile=/dev/null ${SERVER}
sleep 15
done
/usr/bin/python /opt/monroe/client.py
