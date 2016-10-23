Each message sent over the ZMQ bus consists of a topic and a corresponding message identified by the DataId and DataVersion. The suffix of the topic is typically included as a field within the message. Topic is used for ZMQ subscriber filtering, while DataId + DataVersion is used for database mapping and data grouping. The message stored in the database is identical to the ZMQ message (the topic is not stored in the database).

Although only enforced for the mandatory fields below, it is recommended that each "key" in the data field is formatted with CamelCasing, i.e. InterfaceName is preferred over iface_name.

Mandatory fields:
* The common fields: NodeId, Timestamp, DataId and DataVersion.
* SequenceNumber: Used for identifying duplicate messages (i.e., when a message is rebroadcasted).


The following tables describe an overview of the dataformat (DataId+DataVersion) of each message and the corresponding topic names.

Current Data Format and Topics
------------------------------

The following information is currently distributed via the ZMQ bus and stored in the database. See also: https://github.com/MONROE-PROJECT/data-exporter

Topic	DataId	DataVersion	Data Fields	Description/Further Information
Topic: MONROE.META.CONNECTIVITY.iccid
	DataId: MONROE.META.CONNECTIVITY
	DataVersion: 1
	Data fields: ICCID, InterfaceName, MCCMNC, Mode, RSSI
	Description / Further information: Interface, connection events, IP
	
Topic: MONROE.META.DEVICE.MODEM.iccid.UPDATE
	DataId: MONROE.META.DEVICE.MODEM
	DataVersion: 1
	Data fields: CID, DeviceMode, DeviceSubmode, DeviceState, ECIO, ENODEBID, ICCID, InterfaceName, IMSI, IMSIMCCMNC, IMEI, IPAddress, InternalIPAddress, Operator, LAC, RSRP, Frequency, RSRQ, Band, PCI, NWMCCMNC, RSCP, RSSI

Topic: MONROE.META.DEVICE.MODEM.iccid.MODE
	DataId: MONROE.META.DEVICE.MODEM
	DataVersion: 1
	Data fields:

Topic: MONROE.META.DEVICE.MODEM.iccid.SIGNAL
	DataId: MONROE.META.DEVICE.MODEM
	DataVersion: 1
	Data fields: CID, DeviceMode, DeviceSubmode, DeviceState, ECIO, ENODEBID, ICCID, InterfaceName, IMSI, IMSIMCCMNC, IMEI, IPAddress, InternalIPAddress, Operator, LAC, RSRP, Frequency, RSRQ, Band, PCI, NWMCCMNC, RSCP, RSSI

Topic: MONROE.META.DEVICE.MODEM.iccid.LTEBAND
	DataId: MONROE.META.DEVICE.MODEM
	DataVersion: 1
	Data fields: CID, DeviceMode, DeviceSubmode, DeviceState, ECIO, ENODEBID, ICCID, InterfaceName, IMSI, IMSIMCCMNC, IMEI, IPAddress, InternalIPAddress, Operator, LAC, RSRP, Frequency, RSRQ, Band, PCI, NWMCCMNC, RSCP, RSSI

Topic: MONROE.META.DEVICE.MODEM.iccid.ISPNAME
	DataId: MONROE.META.DEVICE.MODEM
	DataVersion: 1
	Data fields: CID, DeviceMode, DeviceSubmode, DeviceState, ECIO, ENODEBID, ICCID, InterfaceName, IMSI, IMSIMCCMNC, IMEI, IPAddress, InternalIPAddress, Operator, LAC, RSRP, Frequency, RSRQ, Band, PCI, NWMCCMNC, RSCP, RSSI

Topic: MONROE.META.DEVICE.MODEM.iccid.IPADDR
	DataId: MONROE.META.DEVICE.MODEM
	DataVersion: 1
	Data fields: CID, DeviceMode, DeviceSubmode, DeviceState, ECIO, ENODEBID, ICCID, InterfaceName, IMSI, IMSIMCCMNC, IMEI, IPAddress, InternalIPAddress, Operator, LAC, RSRP, Frequency, RSRQ, Band, PCI, NWMCCMNC, RSCP, RSSI

Topic: MONROE.META.DEVICE.MODEM.iccid.LOCCHANGE
	DataId: MONROE.META.DEVICE.MODEM
	DataVersion: 1
	Data fields: CID, DeviceMode, DeviceSubmode, DeviceState, ECIO, ENODEBID, ICCID, InterfaceName, IMSI, IMSIMCCMNC, IMEI, IPAddress, InternalIPAddress, Operator, LAC, RSRP, Frequency, RSRQ, Band, PCI, NWMCCMNC, RSCP, RSSI

Topic: MONROE.META.DEVICE.MODEM.iccid.NWMCCMNCCHANGE
	DataId: MONROE.META.DEVICE.MODEM
	DataVersion: 1
	Data fields: CID, DeviceMode, DeviceSubmode, DeviceState, ECIO, ENODEBID, ICCID, InterfaceName, IMSI, IMSIMCCMNC, IMEI, IPAddress, InternalIPAddress, Operator, LAC, RSRP, Frequency, RSRQ, Band, PCI, NWMCCMNC, RSCP, RSSI

Topic: MONROE.META.DEVICE.GPS
	DataId: MONROE.META.DEVICE.GPS
	DataVersion: 1
	Data fields:
		Longitude, Latitude, Altitude, SatelliteCount, SequenceNumber, NMEA, Timestamp (when values where logged by core component).

Topic: MONROE.META.NODE.SENSOR.sensor_name
	DataId: MONROE.META.NODE.SENSOR.sensor_name
	DataVersion: 1
	Data fields: see sensor data
	Description / Further information: Temp sensor update, input voltage, current power draw, (what's available), running experiments, quotas.

Topic: MONROE.META.NODE.EVENT
	DataId: MONROE.META.NODE.EVENT
	DataVersion: 1
	Data fields: see node events
	Description / Further information: Power up and other events.


Cleaning of old docker images
-----------------------------

After building and running docker containers, the system may start filling
up with old instances and images no longer in use. These can be cleaned up with the
following commands:

`docker rm -v $(docker ps -a -q -f status=exited)`
`docker rmi $(docker images -f "dangling=true" -q)`

These commands can also be put in a cleaning-script and put in a common binary directory for convenience.
