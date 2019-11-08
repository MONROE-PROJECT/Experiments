
# Experiment
The experiments measure IP RTT by over NB IOT connections by continuously send ping packets to a configurable server (default 8.8.8.8, google public dns).

The experiment will send 1 Echo Request (ICMP type 8) packet every 5 seconds to a server over the NBIOT interface until aborted.
RTT is measured as the time between the Echo request and the Echo reply
(ICMP type 0) is received from the server.

The experiment is designed to run as a docker container and will only work with pycom LET enabled board (tested with fipy).

The experiment is only as stable as the pycom device (ie fails quite often).

The default values are (can be overridden by a /monroe/config):
```
{
    "guid": "no.guid.in.config.file",  # Should be overridden by scheduler
    "nodeid": "fake.nodeid",
    "server": "8.8.8.8",  # ping target
    "interval": 5000,  # time in milliseconds between successive packets
    "dataversion": 1,
    "size":56,
    "device": "/dev/pycom/board0",
    "apn": "lpwa.telia.iot",
    "type": "LTE.IP",  #LTE.IP or LTE.IPV4V6 defualt LTE.IP
    "band": None,   # scans all bands
    "dataid": "MONROE.EXP.NBPING",
    "export_interval": 5.0,
    "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
    "resultdir": "/monroe/results/",
    "dns_servers": ['8.8.8.8', '4.4.4.4'],
    "DEBUG": False
}
```
All debug/error information will be printed on stdout
depending on the "verbosity" variable.

## Requirements

These directories and files must exist and be read/writable by the user/process
running the container.
/monroe/config
"resultdir" (from /monroe/config see defaults above)    


## Sample output
The experiment will produce a single line JSON object similar to these (pretty printed and added comments here for readability)
### Succesful reply
```
 {
     'Bytes': 56,
     'Host': '8.8.8.8',
     'Rtt': 539.817,
     'SequenceNumber': 0,
     'Timestamp': 1573218956.0079842,
     'Guid': '313.123213.123123.123123',
     'DataId': 'MONROE.EXP.NBPING',
     'DataVersion': 1,
     'NodeId': '9',
     'Iccid': '89450421190211492302',
     'Operator': 'lpwa.telia.iot'
 }
```
### No reply (lost interface or network issues)
```
 {
    'Host': '8.8.8.8',
    'SequenceNumber': 0,
    'Timestamp': 1573218956.0079842,
    'Guid': '313.123213.123123.123123',
    'DataId': 'MONROE.EXP.NBPING',
    'DataVersion': 1,
    'NodeId': '9',
    'Iccid': '89450421190211492302',
    'Operator': 'lpwa.telia.iot'
 }
```
