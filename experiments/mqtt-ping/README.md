# MQTT ping
The purpose of this container is to measure RTT of a MQTT msg.
A prebuilt container can be found at docker hub  : monroe/mqtt-ping

[MQTT](http://mqtt.org/) (Message Queuing Telemetry Transport) is an [OASIS](http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html) and [ISO standard](https://www.iso.org/standard/69466.html) publish-subscribe network protocol that transports messages between devices.

## Input

The default values can be overridden by scheduling parameters

* interface -- default eth0
* broker -- host or ip of mqtt broker, default rtt.se.monroe-system.eu
* id -- preshared key id, default monroe
* psk -- preshared password, default $ecretPa$$word!, default do NOT work on rtt.se.monroe-system.eu
* port -- broker port, default 8883
* nummsg -- Number of messages to send, default 5
* interval -- interval between messages in seconds, default 1 second
* delay -- The grace period to let the subscriber subscribe and allow all messages to arrive, default 10 seconds
    * The total waiting time to get all messages depends on the number of messages
* keepalive -- how often keepalive messages shuld be sent, default 60 seconds)
* msglen -- The payload length, default and minimum 32 char/bytes
    * Techincally a msg consists of a sequence number, a timestamp and a padding (#) to the desired msg length, all encoded as a single utf-8 string (all ASCII).

## Output
The container vill produce three files,
* mqtt_ping-<GUID>-<DATE>.log
    * Stdout
* <GUID>-MONROE.EXP.IOT.MQTT.PING-<ts>.log
    * The receive log
* <GUID>-MONROE.EXP.IOT.MQTT.PING-<ts>.json
Example:
```json
{
  "Guid": "sha256:0b09af15580e40ba6b9d206066b524786618d8e036eb5d1d537e551d68658345.1509351.232.1",
  "NodeId": 232,
  "DataId": "MONROE.EXP.IOT.MQTT.PING",
  "Timestamp": 1592833013.527029,
  "DataVersion": 1,
  "SequenceNumber": 1,
  "Broker": "130.243.27.221",
  "Port": 8883,
  "Interface": "op0",
  "Interval": 1,
  "Loss": 0,
  "NumMsg": 5,
  "WaitDelay": 10,
  "MsgLen": 32,
  "KeepAlive": 60,
  "Delays": [
    1.773862586,
    1.51883848,
    1.827335528,
    1.608375344,
    1.824591702
  ],
  "ICCID": "89450421190211492294",
  "IMSI": "238208700926402",
  "IMEI": "862785043720880",
  "Operator": "Telia",
  "IPAddress": "10.81.32.113",
  "IMSIMCCMNC": 23820,
  "NWMCCMNC": 24001,
  "LAC": 65535,
  "CID": 26869532,
  "RSRP": -111,
  "Frequency": 800,
  "RSSI": -100,
  "RSRQ": -12,
  "DeviceMode": 5,
  "DeviceSubmode": 15,
  "Band": 20,
  "DeviceState": 3,
  "PCI": 100,
  "EARFCN": 6254
}
```
