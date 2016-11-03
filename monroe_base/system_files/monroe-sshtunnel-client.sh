#!/bin/bash
USER=$(whoami)

# Retriving the config
echo "DISCLAIMER: This script will not work unless started by adding the ssh option in the UI"

echo "Getting the tunnelserver details from config file"
CLIENT_KEY=$(jq -r '.["ssh.client.public"]' /monroe/config)
NODEID=$(jq -r '.["nodeid"]' /monroe/config)
TUNNELKEY=$(jq -r '.["_ssh.private"]' /monroe/config)
TUNNELSERVER=$(jq -r '.["ssh.server"]' /monroe/config)
TUNNELCLIENTPORT=$(jq -r '.["ssh.clientport"]' /monroe/config)
TUNNELSERVERPORT=$(jq -r '.["ssh.server.port"]' /monroe/config)
TUNNELUSER=$(jq -r '.["ssh.server.user"]' /monroe/config)
[[ -z  ${NODEID}  ]] && echo "No nodeid exiting" && exit
[[ -z  ${CLIENT_KEY}  ]] && echo "No Client key exiting" && exit
[[ -z  ${TUNNELKEY}  ]] && echo "No TunnelKey exiting" && exit
[[ -z  ${TUNNELSERVER}  ]] && echo "No tunnel server exiting" && exit
[[ -z  ${TUNNELSERVERPORT}  ]] && echo "No tunnel server port exiting" && exit
[[ -z  ${TUNNELUSER}  ]] && echo "No tunnel user exiting" && exit
[[ -z  ${TUNNELCLIENTPORT}  ]] && echo "No client tunnel port exiting" && exit

# Create needed directories
echo "Creating necessary directories"
mkdir -p /${USER}/.ssh
mkdir -p /var/run/sshd

echo "Setting up ssh"
# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/ssh

echo "Adding ssh keys to files"
echo ${CLIENT_KEY} > /${USER}/.ssh/authorized_keys
# Not super secure but since the key is temporary and the information nyway can be
# read from the config file lets leave it as it is.
# The user can not login to the server with these credentials anyway.
echo ${TUNNELKEY} > /${USER}/.ssh/tunnelkey

echo "Starting sshd"
/usr/sbin/sshd -p ${TUNNELCLIENTPORT}

# Figure out ip adresses
echo "Figuring out a working IP"
BINDIP=""
for INT in eth0 wlan0 op0 op1 op2
do
  CHOOSENIF=${INT}
  [[ -z  ${BINDIP}  ]] && BINDIP=$(ip -f inet addr show ${INT} |grep -Po 'inet \K[\d.]+')
done
[[ -z  ${BINDIP}  ]] && echo "No IP exiting" && exit


# Print some diagnostics
echo "#############################"
echo -n "authorized_keys: "
cat /${USER}/.ssh/authorized_keys
echo ""
echo "Tunnelserver : ${TUNNELUSER}@${TUNNELSERVER}:${TUNNELSERVERPORT}"
echo "Clientport : ${TUNNELCLIENTPORT}"
echo "Using IF : ${CHOOSENIF}"
echo "#############################"
echo "To connect :"
echo "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i your_private_key -p ${TUNNELCLIENTPORT} ${USER}@${TUNNELSERVER}"
#Start tunnel and loop forever
while true
do
echo /usr/bin/ssh  -b ${BINDIP} \
                   -NTC \
                   -o ServerAliveInterval=60 \
                   -o ExitOnForwardFailure=yes \
                   -o StrictHostKeyChecking=no \
                   -o  ServerAliveCountMax=3 \
                   -o ConnectTimeout=10 \
                   -o BatchMode=yes \
                   -o UserKnownHostsFile=/dev/null \
                   -i /${USER}/.ssh/tunnelkey \
                   -p ${TUNNELSERVERPORT} \
                   -R \*:${TUNNELCLIENTPORT}:localhost:${TUNNELCLIENTPORT} ${TUNNELUSER}@${TUNNELSERVER}
sleep 15
done
