
# Experiment
The experiments measure IP RTT by continuously send ping
packets to a configurable server (default 8.8.8.8, google public dns).

The experiment will send 1 Echo Request (ICMP type 8) packet per second to a
server over the specified interface until aborted.
RTT is measured as the time between the Echo request and the Echo reply
(ICMP type 0) is received from the server.

The experiment is designed to run as a docker container and will not attempt to
do any active network configuration.
If the Interface does not exist (ie is not UP) when the experiment starts it
will immediately exit.

The default values are (can be overridden by a /monroe/config):
```
{
        "guid": "no.guid.in.config.file",  # Should be overridden by scheduler
        "zmqport": "tcp://172.17.0.1:5556",
        "nodeid": "fake.nodeid",
        "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
        "server": "8.8.8.8",  # ping target
        "interval": 1000,  # time in milliseconds between successive packets
        "dataversion": 1,
        "dataid": "MONROE.EXP.PING",
        "meta_grace": 120,  # Grace period to wait for interface metadata
        "ifup_interval_check": 5,  # Interval to check if interface is up
        "export_interval": 5.0,
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "interfacename": "eth0",  # Interface to run the experiment on
        "interfaces_without_metadata": ["eth0",
                                        "wlan0"]  # Manual metadata on these IF
}
```
Description of the variables in fping_experimenturl_wrapper.py (line 29).

All debug/error information will be printed on stdout
depending on the "verbosity" variable.

## Requirements

These directories and files must exist and be read/writable by the user/process
running the container.
/monroe/config
"resultdir" (from /monroe/config see defaults above)    


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
   "Timestamp": 23123.1212, # time.time()
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
