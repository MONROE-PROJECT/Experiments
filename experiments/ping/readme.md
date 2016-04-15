
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
NodeId, DataId, DataVersion will be appended to the sample output before transmission to the db (by the monroe_exporter function).
Single line printed on multiple lines for readability
```
DataId = "MONROE.EXP.PING"
DataVersion = 1

{
  "InterfaceName": "eth0",
  "SequenceNumber": 6,
  "TimeStamp": 1460723683.108559,
  "Bytes": 84,
  "Rtt": 6.7,
  "Host": "8.8.8.8"
}
```
