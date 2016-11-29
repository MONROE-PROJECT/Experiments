#!/bin/bash

# Author: Jonas Karlsson
# Date: November 2016
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

echo "Retriving configuration"
source /etc/profile
[[ -z  ${USER}  ]] && echo "No USER exiting" && exit
[[ -z  ${SERVERPORT}  ]] && echo "No server port exiting" && exit
[[ -z  ${SCHEDULERURL}  ]] && echo "No scheduler url exiting" && exit
[[ -z  ${UPDATEFREQ}  ]] && echo "No key update frequencey defined exiting" && exit
[[ ! -f ${CERT} ]] && echo "No tunnel-server cert/pem exiting" && exit
[[ ! -f ${KEY} ]] && echo "No tunnel-server key exiting" && exit
[[ ! -d "/home/${USER}/.ssh" ]] && echo "No user home directory (.ssh)" && exit

AUTHKEY_FILE="/home/${USER}/.ssh/authorized_keys"
#CURL_OPT="--key ${KEY} --cert ${CERT} --insecure ${SCHEDULERURL}"
CURL_OPT="--key ${KEY} --cert ${CERT} ${SCHEDULERURL}"
JQ_OPT="--raw-output .[]"

echo "Starting sshd on port ${SERVERPORT}"
/usr/sbin/sshd -p ${SERVERPORT}

# Print some diagnostics
echo "#############################"
echo "USER : ${USER}"
echo "SSHPORT : ${SERVERPORT}"
echo "Scheduler URL : ${SCHEDULERURL}"
echo "Delay between schdeduler pulls : ${UPDATEFREQ}"
echo -n "Cert used : "
cat ${CERT}
echo ""
echo -n "Key used : "
cat ${KEY}
echo ""
echo "Key retrival command command : curl ${CURL_OPT} | jq ${JQ_OPT} > ${AUTHKEY_FILE}"


#Start tunnel and loop forever
while true
do
  echo "Retriving pubkeys from scheduler"
  curl ${CURL_OPT} | jq ${JQ_OPT} > ${AUTHKEY_FILE}
  echo "###################"
  echo "Authorized keys : "
  cat ${AUTHKEY_FILE}
  echo "Tunnel Connections:"
  netstat -tnpa | grep 'ESTABLISHED'|grep ":${SERVERPORT}"
  echo "Client Connections:"
  netstat -tnpa | grep 'ESTABLISHED'|grep -v ":${SERVERPORT}"
  echo "Sleeping ${UPDATEFREQ} seconds"
  sleep ${UPDATEFREQ}
done
echo " SSH tunnel-server finished"
