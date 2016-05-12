
# Experiment

The experiments measure IP RTT by continuously send ping
packets to host 8.8.8.8 (google public dns).

The experiment will send 1 Echo Request (ICMP type 8) packet per second to
host 8.8.8.8 over the specified interface until aborted.
RTT is measured as the time between the Echo request and the Echo reply
(ICMP type 0) is received from the server.

The experiment require Interface Name as a mandatory parameter.

The experiment is designed to run as a docker container and will not attempt to
do any active network configuration.
If the Interface does not exist (ie is not UP) when the experiment starts it
will immediately exit.

## Requirements

These directories must exist and be writable by the user/process running
the experiment.
/output/    
/tmp/    


## Example usage
```bash
fping -I eth0 -D -p 1000 -l 8.8.8.8 | python ./fping_json_formatter.py eth0
```

## Docker misc usage

docker ps  # list running images    
docker exec -it [container id] bash   # attach to running container

## Sample output
Single line printed on multiple lines for readability
```
{
 "DataId": "MONROE.EXP.PING",
 "InterfaceName": "eth0", 
 "SequenceNumber": 70,
 "Rtt": 6.47,
 "IMSIMCCMNC": 24214,
 "DataVersion": 1,
 "NWMCCMNC": 24214,
 "NodeId": "48",
 "Bytes": 84,
 "Operator": "Telenor",
 "Host": "8.8.8.8",
 "TimeStamp": 1463048694.806557,
 "IMEI": "990004610244323",
 "ICCID": "89470715000000631700",
 "IMSI": "242140000163170"
}
```
