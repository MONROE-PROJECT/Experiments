#!/bin/bash
# -*- coding: utf-8 -*-

# Author: Ali Safari Khatouni
# Date: October 2017
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project
# The container need two parameters operator and country like the format should be 
# as the dictionary in metadata.py
# "operator":"TIM","country":"IT"


NODEID=`cat /nodeid`
echo "NODEID  $NODEID"

# Try to check connectivity of all interfaces
for INTERFACE in $(ip -o link show | grep  'state UP'  | grep -v -E 'metadata|lo|eth1' | awk -F': ' '{print $2}' | cut -d "@" -f 1);
do
curl --interface $INTERFACE http://ipecho.net/plain -q -m 1 --resolve http://ipecho.net:80:146.255.36.1
done

ifconfig 
arp -n 
route -n

cat /monroe/config

echo "Start metadata listener! "
python metadata.py 
echo "Got all metadata"

cat *metadata
cat *servers
cat python.log


ifconfig 
arp -n 
route -n
ls -rtl 

for FILE in facetime_audio_3G.pcap fbmessanger_audio_3G.pcap  whatsapp_audio_3G.pcap facetime_video_3G.pcap fbmessanger_video_3G.pcap whatsapp_video_3G.pcap;
do
	for INTERFACE in $(ip -o link show | grep  'state UP'  | grep -v -E 'metadata|lo|eth1' | awk -F': ' '{print $2}' | cut -d "@" -f 1);
	do
		S_MAC=$(ip addr show $INTERFACE | grep link/ether | awk '{print $2}' | xargs )
		D_MAC=$(arp -n  | grep -v incomplete |grep C | grep ether | grep $INTERFACE | tr -s " " | cut -d " " -f3 | grep -v  $INTERFACE | tr "\n" " "| cut -d" " -f1 | xargs)
		S_IP=$(ip addr show $INTERFACE | grep -w inet | awk '{print $2}' | cut -d "/" -f1 | xargs)
		METADATA="$INTERFACE.metadata"
		echo "CHECK  S_MAC $S_MAC --S_IP $S_IP --D_MAC $D_MAC" 
		if [[ -e $INTERFACE.servers && -n "$S_MAC" && -n "$S_IP" && -n "$D_MAC" && -e $METADATA ]] ; then 
			SERVERS=$(cut -d " " -f 1,2 $INTERFACE.servers)

			PCAP_FILE=$INTERFACE"_"$FILE
			# Run tcpdump for servcie
			echo "CHECK  tcpdump -l -U -i $INTERFACE -w $PCAP_FILE"
			tcpdump -l  -U -i $INTERFACE -w $PCAP_FILE &
			TCPDUMP_PID=$!

			for SERVER in $SERVERS;
			do
				echo "CHECK $FILE $INTERFACE $SERVER"				
				echo "CHECK  S_MAC $S_MAC --S_IP $S_IP --D_MAC $D_MAC" 

				PUB_IP=$(curl --interface $INTERFACE http://ipecho.net/plain -q -m 3 --resolve http://ipecho.net:80:146.255.36.1)
				CONCAT_STRING=", 'Test' : '$FILE' , 'IP' : '$PUB_IP', 'Node' : '$NODEID' }"
				START_MSG=`sed  "s/}/$CONCAT_STRING/g" $METADATA`
				echo "echo -n START = $START_MSG |  nc -q1 -s $S_IP $SERVER 50007"

				echo -n "START = $START_MSG" |  nc -q1 -s $S_IP $SERVER 50007

				# Manually saet the mac and IP here for each experiment
				echo "CHECK  tcprewrite --enet-dmac=$D_MAC --enet-smac=$S_MAC   --infile=$FILE --outfile=tmp.pcap"

				tcprewrite --enet-dmac=$D_MAC --enet-smac=$S_MAC   --infile=$FILE --outfile=tmp.pcap 

				echo "CHECK  tcpprep --mac=$S_MAC   --pcap=tmp.pcap --cachefile=input.cache"

				tcpprep --mac=$S_MAC   --pcap=tmp.pcap --cachefile=input.cache

				echo "CHECK  tcprewrite --endpoints=$S_IP:$SERVER --fixlen=pad --skipbroadcast --enet-vlan=del  --cachefile=input.cache  --infile=tmp.pcap --outfile=output.pcap"

				tcprewrite --endpoints=$S_IP:$SERVER --fixlen=pad --skipbroadcast --enet-vlan=del  --cachefile=input.cache  --infile=tmp.pcap --outfile=output.pcap 

				echo "CHECK  tcpreplay --intf1=$INTERFACE  output.pcap"

				tcpreplay --intf1=$INTERFACE  output.pcap
				CONCAT_STRING=", 'Test' : '$FILE' , 'IP' : '$PUB_IP', 'Node' : '$NODEID' }"
				START_MSG=`sed  "s/}/$CONCAT_STRING/g" $METADATA`

				echo "echo -n STOP = $START_MSG |  nc -q1 -s $S_IP $SERVER 50007"

				echo -n "STOP = $START_MSG" |  nc -q1 -s $S_IP $SERVER 50007

			done
			# Stop tcpdump
			# fake traffic to force the tcpdump dumps captured data into output file
			curl --interface $INTERFACE http://ipecho.net/plain -q -m 2 --resolve http://ipecho.net:80:146.255.36.1
			curl --interface $INTERFACE http://ipecho.net/plain -q -m 1 --resolve http://ipecho.net:80:146.255.36.1
			sleep 2
			kill -9 $TCPDUMP_PID 
			sleep 1
			# Copy all data into result directory 
			cp $PCAP_FILE /monroe/results/
			cp $METADATA /monroe/results/
			cp $INTERFACE.servers /monroe/results/
			sleep 1
		fi
	done
done