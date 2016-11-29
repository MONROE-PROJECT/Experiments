#!/bin/bash

# Author: Jonas Karlsson
# Date: November 2016
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

echo "DISCLAIMER: This script will not work unless started by adding the ssh option in the UI"

# Port offset must match the start of the port range on the tunnel server and what is displayed in the UI
USER=$(whoami)
PORTOFFSET=30000

# Retriving the config
echo "Getting the tunnelserver details from config file"
TUNNELSERVER=$(jq -r '.["ssh"]["server"]' /monroe/config)
TUNNELSERVERPORT=$(jq -r '.["ssh"]["server.port"]' /monroe/config)
TUNNELUSER=$(jq -r '.["ssh"]["server.user"]' /monroe/config)
# Tunnel key is special since we need to preserve the \n and -r strips the newline
TUNNELKEY=$(jq '.["_ssh.private"]' /monroe/config)
# Use bash native prefix/suffic removal
TUNNELKEY="${TUNNELKEY%\"}"
TUNNELKEY="${TUNNELKEY#\"}"

CLIENT_KEY=$(jq -r '.["ssh"]["client.public"]' /monroe/config)
# Needed for calculating the port below
NODEID=$(jq -r '.["nodeid"]' /monroe/config)

[[ -z  ${NODEID}  ]] && echo "No nodeid exiting" && exit
TUNNELCLIENTPORT=$((${NODEID} + ${PORTOFFSET}))
[[ -z  ${TUNNELCLIENTPORT}  ]] && echo "No client tunnel port exiting" && exit
[[ -z  ${CLIENT_KEY}  ]] && echo "No Client key exiting" && exit
[[ -z  ${TUNNELKEY}  ]] && echo "No TunnelKey exiting" && exit
[[ -z  ${TUNNELSERVER}  ]] && echo "No tunnel server exiting" && exit
[[ -z  ${TUNNELSERVERPORT}  ]] && echo "No tunnel server port exiting" && exit
[[ -z  ${TUNNELUSER}  ]] && echo "No tunnel user exiting" && exit

# Create needed directories
echo "Creating necessary directories for ssh"
mkdir -p /${USER}/.ssh
mkdir -p /var/run/sshd

echo "Setting up ssh keys"
echo ${CLIENT_KEY} > /${USER}/.ssh/authorized_keys
# Not super secure but since the key is temporary and the information anyway can be
# read from the config file lets leave it as it is.
# The user can not login to the server with these credentials.
# -e to preserve newlines
echo -e ${TUNNELKEY} > /${USER}/.ssh/tunnelkey
chmod 0600 /${USER}/.ssh/tunnelkey

echo "Starting sshd on port ${TUNNELCLIENTPORT}"
/usr/sbin/sshd -p ${TUNNELCLIENTPORT}

# Figure out a ip adresses
echo -e "Figuring out a working IP/Interface : "
BINDIP=""
PINGOK=""
for INT in eth0 wlan0 op0 op1 op2
do
  if [[ -z  ${PINGOK}  ]]
  then
    CHOOSENIF=${INT}
    BINDIP=$(ip -f inet addr show ${INT} |grep -Po 'inet \K[\d.]+')
    [[ ${BINDIP} ]] && PINGOK=$(fping -S ${BINDIP} ${TUNNELSERVER} -r1|grep alive)
  fi
done
[[ -z  ${BINDIP}  ]] && echo "No IP exiting" && exit
[[ -z  ${PINGOK}  ]] && echo "Cannot ping ${TUNNELSERVER} from ${BINDIP} exiting" && exit
echo "Using IP ${BINDIP} on interface ${CHOOSENIF}"

# Print some diagnostics
echo "#############################"
echo -n "authorized_keys: "
cat /${USER}/.ssh/authorized_keys
echo ""
echo "Tunnelserver : ${TUNNELUSER}@${TUNNELSERVER}:${TUNNELSERVERPORT}"
echo "Using local sshd : ${TUNNELCLIENTPORT} calculated with offset ${PORTOFFSET}"
echo "Binding ssh-tunnel to : ${BINDIP} on interface ${CHOOSENIF}"
echo "#############################"
echo "To connect :"
echo "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i your_private_key -p ${TUNNELCLIENTPORT} ${USER}@${TUNNELSERVER}"
#Start tunnel and loop forever
while true
do
/usr/bin/ssh   \
              -b ${BINDIP} \
              -NTC \
              -o ServerAliveInterval=60 \
              -o ExitOnForwardFailure=yes \
              -o StrictHostKeyChecking=no \
              -o ServerAliveCountMax=3 \
              -o ConnectTimeout=10 \
              -o BatchMode=yes \
              -o UserKnownHostsFile=/dev/null \
              -i /${USER}/.ssh/tunnelkey \
              -p ${TUNNELSERVERPORT} \
              -R \*:${TUNNELCLIENTPORT}:localhost:${TUNNELCLIENTPORT} ${TUNNELUSER}@${TUNNELSERVER}
sleep 15
done
echo " SSH tunnel script finished"
