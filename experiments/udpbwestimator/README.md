#udpbwestimator

udpbwestimator is an experiment setup to estimate available bandwidth for a 
particular network interface. It consists of two applications, a receiver and 
a traffic generator (server). The receiver initiates the connections and requests 
the server for traffic. Then in each second, the server  sends a burst of UDP packets 
back to back to the receiver, which follows the packet arrival times and estimates 
the available bandwidth.

## Input

The receiver accepts the following input from the command line

* -c : Number of back to back packets to be sent  in each second.
* -b : number of bust to be sent.
* -l : Payload length in bytes.
* -s : Source IP to bind to.
* -o : source port.
* -d : Destination IP.
* -p : Destination port.
* -w : Provide an optional filename for writing the packet receive times. 

## Output

The experiment will produce a single line JSON object similar to the following

```
{ "CID" : 33346602,
  "DataId" : "MONROE.EXP.UDPBWESTIMATOR",
  "DataVersion" : 1,
  "DeviceMode" : 5,
  "DeviceState" : 3,
  "Guid" : "sha256:872af8c8b8f1635be6936a111b5fa838071e6f42cb317e9db1d9bb0c7db31425.93321.204.1",
  "IMEI" : "864154023639966",
  "IMSI" : "240016025247086",
  "IMSIMCCMNC" : 24001,
  "IPAddress" : "78.79.63.124",
  "Iccid" : "89460120151010468086",
  "InterfaceName" : "usb0",
  "InternalIPAddress" : "192.168.68.118",
  "InternalInterface" : "op1",
  "LAC" : 2806,
  "NWMCCMNC" : 24202,
  "NodeId" : "204",
  "Operator" : "NetCom",
  "RSRP" : -72,
  "RSRQ" : -7,
  "RSSI" : -49,
  "SequenceNumber" : 1,
  "Timestamp" : 1479312368.633218,
  "bw" : "48.41 38.98 36.44 50.00 30.20 45.21 47.02 37.89 44.37 28.90 25.91 38.57 48.74 39.94 43.37 37.94 43.81 39.60 52.00 47.55 48.20 34.85 41.44 47.60 57.26 46.11 45.66 52.04 37.43 49.67 33.56 50.35 41.11 51.63 45.33 104.01 45.73 49.95 50.37 38.57 29.45 50.95 54.95 45.42 47.13 34.30 46.10 103.68 79.75 45.72 52.03 30.38 50.21 36.96 71.51 54.66 39.26 44.12 45.18 39.93"
}
```
