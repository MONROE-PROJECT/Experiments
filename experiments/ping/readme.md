
# Experiment
The experiments measure IP RTT by continuously send ping
packets to host 8.8.8.8 (google public dns).

The experiment will send 1 Echo Request (ICMP type 8) packet per second to
host 8.8.8.8 over the specified interface until aborted.
RTT is measured as the time between the Echo request and the Echo reply
(ICMP type 0) is received from the server.

The experiment is designed to run as a docker container and will not attempt to
do any active network configuration.
If the Interface does not exist (ie is not UP) when the experiment starts it
will immediately exit.
Evaluate http download speed.

The default values are (can be overridden by a /monroe/config):
```
{
    "dataid": "MONROE.EXP.PING",
    "dataversion": 1,
    "export_interval": 5.0,
    "guid": "no.guid.in.config.file",
    "ifup_interval_check": 5,
    "interfacename": "eth0",
    "interfaces_without_metadata": [
        "eth0",
        "wlan0"
    ],
    "meta_grace": 120,
    "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
    "resultdir": "/monroe/results/",
    "verbosity": 2,
    "zmqport": "tcp://172.17.0.1:5556"
}

```
Description of the variables in fping_experimenturl_wrapper.py (line 29).

All debug/error information will be printed on stdout
depending on the "verbosity" variable.

## Requirements

These directories and files must exist and be read/writable by the user/process
running the container.
/opt/monroe/config
"resultdir" (from /opt/monroe/config see defaults above)    


## The experiment will execute a statement similar to running fping like this
```bash
fping -I eth0 -D -p 1000 -l 8.8.8.8
```

## Docker misc usage
docker ps  # list running images    
docker exec -it [container id] bash   # attach to running container

## Sample output
Single line, pretty printed and added comments here for readability
```
 {
   "Guid": "313.123213.123123.123123", # exp_config['guid']
   "TimeStamp": 23123.1212, # time.time()
   "Iccid": 2332323, # meta_info["ICCID"]
   "Operator": "Telia", # meta_info["Operator"]
   "NodeId" : "9", # exp_config['nodeid']
   "DataId": "MONROE.EXP.PING",
   "DataVersion": 1,
   "SequenceNumber": 70,
   "Rtt": 6.47,
   "Bytes": 84,
   "Operator": "Telenor",
   "Host": "8.8.8.8",
 }
```
