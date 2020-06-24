# Monroe-coap 
Monroe-coap container allows to exchange information among IOT enabled monroe nodes using The Constrained Application Protocol (CoAP) (RFC 7252). Like HTTP, CoAP is based on the wildly successful REST model: Servers make resources available under a URL, and clients access these resources using methods such as GET, PUT, POST, and DELETE. In this container client (monroe node) put a resource in the CoAP server and the server acknowldeges. From the exchanges, the monroe node determines the delay of massage exchange. The container calculates both one way and both way delays. One way delay  is subject to time synchronization error between the node and the server. 


## Input

The default input values are (can be overridden by a /monroe/config):
```bash
{
        "guid": "no.guid.in.config.file",  # Should be overridden by scheduler
        "zmqport": "tcp://172.17.0.1:5556",
        "nodeid": "fake.nodeid",
        "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
        "server": "xx.xx.xx.xx",  # ping target
        "interval": 1000,  # time in milliseconds between successive packets
        "dataversion": 2,
        "msgLen":100,
        "msgInterval":2,
        "numMsgs":4,
        "time": 100, #max time for exps
        "dataid": "MONROE.EXP.COAP",
        "meta_grace": 120,  # Grace period to wait for interface metadata
        "exp_grace": 120,  # Grace period before killing experiment
        "ifup_interval_check": 5,  # Interval to check if interface is up
        "export_interval": 5.0,
        "verbosity": 3,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "modeminterfacename": "InternalInterface",
        "interfacename": "op0",  # Interface to run the experiment on
        "allowed_interfaces": ["op0"],
        "interfaces_without_metadata": ["eth0"]  # Manual metadata on these IF
        }
```
By default the monroe node sends 4 messages back to back with an interval of 2 sec, each message is 100 bytes long.

## Output
The experiment generates a single JSON file like the following

```bash
{
  "DataId": "MONROE.EXP.COAP",
  "owd": [
    0.3721613883972168,
    0.5116682052612305,
    0.7049727439880371,
    0.3427853584289551
  ],
  "NodeId": "232",
  "rtt": [
    0.60812,
    0.580543,
    0.778988,
    0.517644
  ],
  "Iccid": "89450421190211492294",
  "LAC": 65535,
  "msgLen": 100,
  "msgInterval": 2,
  "deviceMode": 5,
  "RSRQ": -8,
  "RSRP": -111,
  "DataVersion": 2,
  "Timestamp": 1592917306.290395,
   "server": "xx.xx.xx.xx",
  "deviceSubMode": 15,
  "numMsgs": 4,
  "Operator": "Telia",
  "RSSI": -102,
  "Guid": "sha256:e7d8387c821bff1e5d1920eccf9a1a56f91d0367c3c776c8733c0de404022ec5.1509357.232.1",
  "IPAddress": "10.81.167.89"
}
```

