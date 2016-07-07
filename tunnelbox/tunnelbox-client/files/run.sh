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
BINDIP=$(ip -f inet addr show eth0 |grep -Po 'inet \K[\d.]+')
[[ -z  $BINDIP  ]] && BINDIP=$(ip -f inet addr show op0 |grep -Po 'inet \K[\d.]+')
[[ -z  $BINDIP  ]] && BINDIP=$(ip -f inet addr show op1 |grep -Po 'inet \K[\d.]+')
[[ -z  $BINDIP  ]] && BINDIP=$(ip -f inet addr show op2 |grep -Po 'inet \K[\d.]+')

[[ -z  $BINDIP  ]] && echo "No IP exiting" && exit

SERVER=$(/usr/bin/python /opt/monroe/client.py ${BINDIP})

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
