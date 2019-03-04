#!/usr/bin/env bash
cd /opt/monroe/
NODEID=$(cat /nodeid)
LOG_FILE=/monroe/results/nodetest-${NODEID}-$(date +%F).log
echo "Teeing stdout to ${LOG_FILE}"
exec &> >(tee -a "$LOG_FILE")
echo "**********************************"
echo "Starting node Validation : $(date)"
echo "NodeId : ${NODEID}"
echo "Interfaces : $(ls /sys/class/net/|tr '\n' ',')"
echo "DNS : $(cat /dns|grep listen)"
for int in $(ls /sys/class/net/)
do
    echo "Interface : $int"
    echo "--> IP : $(ifconfig $int |grep inet|grep -v inet6|awk '{print $2}')"
    if [[ "$int" != "lo" ]]
    then
        echo "--> Logging tcdump in /monroe/results/tcpdump-$int.pcap"; tcpdump -i $int -U -w /monroe/results/tcpdump-$int.pcap &> /dev/null &
        if [[ "$int" != "metadata" ]]
        then
            sleep 5 # to let tcpdump start properly
            echo "--> DNS : $(cat /dns|grep $int|tr '\n' ',')"
            echo "--> PING : $(fping -I $int 8.8.8.8)"
        fi
    fi
done
echo -e "Disk : \n $(df -h)"
echo -e "Mem : \n $(free -h)"
echo -e "Cpu : \n $(cat /proc/cpuinfo)"
grep -q ^flags.*\ hypervisor /proc/cpuinfo && echo "--> This machine is a VM"
echo -e "--> 10 highest CPU processes : \n $(ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head -n11)"
echo "Kernel : $(uname -a)"
# Is neat proxy enabled 
if curl --silent --output /dev/null 172.17.0.1:45888/cib
then
	echo -e "neat enabled : yes \n"
	echo -e "--> (neat) PIB : \n $(curl --silent 172.17.0.1:45888/pib |jq .[])"
	echo -e "--> (neat) CIB : \n $(curl --silent 172.17.0.1:45888/cib |jq .[])"	
#else
#	echo -e "neat enabled : no \n"
fi
# Is there any Pycom boards connected
if [ -d "/dev/pycom" ]
then 
	echo -e "IoT enabled (Pycom LoRa/NB-Iot) : yes \n"
	echo -e "--> (IoT) boards connected $(ls /dev/pycom |wc -l)"
#else
#	echo -e "IoT enabled (Pycom LoRa/NB-Iot) : no \n"
fi
echo -e "CONFIG : \n $(cat /monroe/config|jq .)"
echo "Routing :"
echo -e "--> route -n : \n $(route -n)"
echo -e "--> ip route : \n $(ip route)"
echo -e "--> ip route tables : \n $(ip route show table all)"
if [[ ! -z $(cat /monroe/config|jq -r '.vm // empty') ]]
then 
    echo -e "--> (vm) Routing config : \n $(cat /opt/monroe/setup-routing.sh)"
    echo -e "--> (vm) Interfaces config : \n $(cat /etc/network/interfaces.d/*)"
    echo -e "--> (vm) Mounts config : \n $(cat /opt/monroe/setup-mounts.sh)"
fi

#Metadata is easier from python so going for that
#echo "Metadata: Listening for all metadata for 120 s"
#timeout 120s /usr/bin/python -u /opt/monroe/metadata  
if [[ "$(ls /sys/class/net/|grep metadata)" != "" ]]
then
    timeout 120s /usr/bin/python -u metadata.py || echo "Metadata: No info in 120 seconds"
else
    echo "Metadata : No metadata interface"
fi

echo "Ending node Validation : $(date)"
echo "**********************************"
exit 0
