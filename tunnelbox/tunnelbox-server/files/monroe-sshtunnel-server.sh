#!/bin/bash
source /etc/profile
[[ -z  ${USER}  ]] && echo "No USER exiting" && exit
[[ -z  ${SERVERPORT}  ]] && echo "No server port exiting" && exit
[[ -z  ${SCHEDULERURL}  ]] && echo "No scheduler url exiting" && exit
[[ -z  ${UPDATEFREQ}  ]] && echo "No key update frequencey defined exiting" && exit
[[ ! -f ${CERT} ]] && echo "No tunnel-server cert/pem exiting" && exit
[[ ! -f ${KEY} ]] && echo "No tunnel-server key exiting" && exit
[[ ! -d "/home/${USER}/.ssh" ]] && echo "No user home directory (.ssh)" && exit

AUTHKEY_FILE="/home/${USER}/.ssh/authorized_keys"
CURL_OPT="--key ${KEY} --cert ${CERT} --insecure ${SCHEDULERURL}"
JQ_OPT="--raw-output .[]"
echo "Starting sshd"
/usr/sbin/sshd -p ${SERVERPORT}

# Print some diagnostics
echo "#############################"
echo "USER : ${USER}"
echo "SSHPORT : ${SERVERPORT}"
echo "Scheduler URL : ${SCHEDULERURL}"
echo "Delay between pulls : ${UPDATEFREQ}"
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
  #curl ${CURL_OPT} | jq ${JQ_OPT} > ${AUTHKEY_FILE}
  cat /opt/monroe/curlresults.txt | jq ${JQ_OPT} > ${AUTHKEY_FILE}
  echo "###################"
  echo "Authorized keys : "
  cat ${AUTHKEY_FILE}
  echo "Tunnel Connections:"
  netstat -tnpa | grep 'ESTABLISHED'|grep ":${SERVERPORT}"
  echo "Client Connections:"
  netstat -tnpa | grep 'ESTABLISHED'|grep -v ":${SERVERPORT}"
  sleep ${UPDATEFREQ}
done
echo " SSH tunnel-server finished"
