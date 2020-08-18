#!/usr/bin/env bash
cd /opt/monroe/
NODEID=$(cat /nodeid 2>/dev/null)
CONFIG="$(cat /monroe/config 2>/dev/null)"
INTERFACE=$(echo $CONFIG | jq -r '.interface // empty')
BROKER=$(echo $CONFIG | jq -r '.broker // empty')
ID=$(echo $CONFIG | jq -r '.id // empty')
PSKPW=$(echo $CONFIG | jq -r '.psk // empty')
PORT=$(echo $CONFIG | jq -r '.port // empty')
NUMMSG=$(echo $CONFIG | jq -r '.nummsg // empty')
INTERVAL=$(echo $CONFIG | jq -r '.interval // empty')
GUID=$(echo $CONFIG | jq -r '.guid // empty')
DELAY=$(echo $CONFIG | jq -r '.delay // empty')
KEEPALIVE=$(echo $CONFIG | jq -r '.keepalive // empty')
MSGLEN=$(echo $CONFIG | jq -r '.msglen // empty')

SUBLOG=/sub.log
JSONLOG=/results.json
DATAID="MONROE.EXP.IOT.MQTT.PING"

#Default Values
if [ -z "$NODEID" ]; then NODEID="fake.dev"; fi
if [ -z "$BROKER" ]; then BROKER="rtt.se.monroe-system.eu"; fi
if [ -z "$ID" ]; then ID="monroe"; fi
if [ -z "$PORT" ]; then PORT=8883; fi
if [ -z "$PSKPW" ]; then PSKPW='$ecretPa$$word!'; fi
if [ -z "$NUMMSG" ]; then NUMMSG=5; fi
if [ -z "$INTERVAL" ]; then INTERVAL=1; fi
if [ -z "$INTERFACE" ]; then INTERFACE="eth0"; fi
if [ -z "$GUID" ]; then GUID="fake.dev"; fi
if [ -z "$DELAY" ]; then DELAY=10; fi
if [ -z "$KEEPALIVE" ]; then KEEPALIVE=60; fi
if [ -z "$MSGLEN" ] || (( $MSGLEN < 32 )); then MSGLEN=32; fi
if (( $DELAY < 60 ))
then
  SUBDELAY=60
else
  SUBDELAY=$DELAY
fi
# http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html#_Toc398718023  max 256 MB
# Conversions
PSK="$(xxd -pu <<< $PSKPW)"
# strip away EOL ie 0a
PSK="${PSK::-2}"
# Get interface IP address
INTIP=$(ip -f inet addr show $INTERFACE | grep -Po 'inet \K[\d.]+')

LOG_FILE=/monroe/results/mqtt_ping-${NODEID}-$(date +%F).log
echo "Teeing stdout to ${LOG_FILE}"
exec &> >(tee -a "$LOG_FILE")
echo "**********************************"
echo "Starting mqtt ping : $(date)"
echo "NodeId : ${NODEID}"
echo "Config : $CONFIG"
echo "Interfaces up : $(ls /sys/class/net/|tr '\n' ',')"
echo "Starting experiment : $(date)"
echo -n "Starting subscriber : "
rm -f $SUBLOG
subtotdelay=$(($NUMMSG*$INTERVAL*2+2*$SUBDELAY))
echo -e "# MSG : Send TS\tReceive TS\tTot msg: $NUMMSG\tINTERVAL: $INTERVAL s" > $SUBLOG
timeout $subtotdelay stdbuf -oL mosquitto_sub -k $KEEPALIVE -A $INTIP -h $BROKER -t "Monroe-$NODEID" -p $PORT --psk-identity $ID --psk $PSK -R -C $NUMMSG -F "%p\t%U" | stdbuf -oL tr -d '#' >> $SUBLOG &
subpid=$!
echo " ok (sleeping $SUBDELAY s)"
# Puttings this here so to not waste time when executing the experiment
IFMETA=$(timeout $SUBDELAY /opt/monroe/metadata 2>/dev/null |grep --line-buffered MONROE.META.DEVICE.MODEM |grep --line-buffered UPDATE | grep --line-buffered $INTERFACE | cut -d' ' -f2- | head -n1)
echo "Interface ($INTERFACE) metadata: $IFMETA"
echo -n "Publishing msgs : "
start=$(date +%s.%N)
for i in $(seq 1 $NUMMSG)
do
  echo -n "."
  ts="$i : $(date +%s.%N)"
  pad=$(printf '%*s' "$MSGLEN")
  pad=${pad// /#}
  msg="$ts$pad"
  mosquitto_pub -k $KEEPALIVE -A $INTIP -h $BROKER -t "Monroe-$NODEID" -p $PORT --psk-identity $ID --psk $PSK -m "${msg:0:$MSGLEN}"
  sleep $INTERVAL
done
now=$(date +%s.%N)
echo " (sent $i msgs in  $(echo "$now-$start" | bc -l) s) ok"
start=$(date +%s.%N)
#It took approax $NUMMSG*$INTERVAL to send the messages so we only wait $NUMMSG*$INTERVAL+2*DELAY
echo -n "Waiting some time for messages to arrive (at max $subtotdelay seconds) :"
wait $subpid
sync
now=$(date +%s.%N)
echo " waited $(echo "$now-$start" | bc -l) seconds"
echo "Got these mesages :"
cat $SUBLOG

echo -n "Calculating loss: "
loss=$(echo "100-($(cat $SUBLOG|wc -l) - 1)/$NUMMSG*100.0" |bc -l)
echo "lost $loss% of $NUMMSG packets"
INTERVALs=$(cat $SUBLOG | awk '!/#/{ print("(",$4,"-",$3,")") }'|bc -l)
ts=$(date +%s.%N)
CURATEDIFMETA=$(echo $IFMETA | jq 'del( . ["SequenceNumber", "Timestamp", "DataVersion", "DataId", "InternalInterface", "InterfaceName"] )')
RES=$(jo -p Guid=$GUID \
      NodeId=$NODEID \
      DataId=$DATAID \
      Timestamp=$ts \
      DataVersion=1 \
      SequenceNumber=1 \
      Broker=$BROKER \
      Port=$PORT \
      Interface=$INTERFACE \
      Interval=$INTERVAL \
      Loss=$loss \
      NumMsg=$NUMMSG \
      WaitDelay=$DELAY \
      MsgLen=$MSGLEN \
      KeepAlive=$KEEPALIVE \
      Delays=$(jo -a $INTERVALs))
echo $RES $CURATEDIFMETA | jq -s add | tee $JSONLOG
mv $SUBLOG /monroe/results/$NODEID-$DATAID-$ts.log
mv $JSONLOG /monroe/results/$NODEID-$DATAID-$ts.json
sync
echo "Ending mqtt_ping test : $(date)"
echo "**********************************"
exit 0
