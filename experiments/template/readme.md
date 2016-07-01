
# Experiment
A template to show of some of the capabilities of the Monroe platform.

The experiment will download a url (file) over http using curl.
The default values are (can be overridden by providing /monroe/config):
```
{
        # The following value are specific to the monroe platform
        "guid": "no.guid.in.config.file",  # Overridden by scheduler
        "nodeid": "no.nodeid.in.config.file",  # Overridden by scheduler
        "storage": 104857600,  # Overridden by scheduler
        "traffic": 104857600,  # Overridden by scheduler
        "script": "jonakarl/experiment-template",  # Overridden by scheduler
        "zmqport": "tcp://172.17.0.1:5556",
        "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
        "gps_metadata_topic": "MONROE.META.DEVICE.GPS",
        # "dataversion": 1,  #  Version of experiment
        # "dataid": "MONROE.EXP.JONAKARL.TEMPLATE",  #  Name of experiement
        "meta_grace": 120,  # Grace period to wait for interface metadata
        "exp_grace": 120,  # Grace period before killing experiment
        "meta_interval_check": 5,  # Interval to check if interface is up
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        # These values are specic for this experiment
        "operator": "Telenor SE",
        "url": "http://193.10.227.25/test/1000M.zip",
        "size": 3*1024 - 1,  # The maximum size in Kbytes to download
        "time": 3600  # The maximum time in seconds for a download
}
```
The download will abort when either size OR time OR actual size of the "url" is
 downloaded.

All debug/error information will be printed on stdout
 depending on the "verbosity" variable.

## Overview of code structure
The experiment consists of one main process and two sub processes.
 1. One process listen to modem and gps information
 3. One process executes the experiment
 4. The main thread are managing the other threads

### Information sharing between processes
The information are shared between the processes by two thread safe
datastructures (a python "Manager" object).
For modem information the latest metadata update (for the specified operator)
are stored in a dictionary.
The gps information are stored in a list that are continuously appended as
information is received.

### The Metadata (sub)process
The responsibility for this process is to:
 1. Listen to gps and modem messages sent on the ZeroMQ bus
 2. Update the shared datastructures

### The experiment (sub)process
The responsibility for this process is to:
 1. Get information from (read) the shared datastructures
 2. run the experiment
 3. save the result when finished


## Requirements

These directories and files must exist and be read/writable by the user/process
running the container:
 * /monroe/config (added by the scheduler in the nodes)
 * "resultdir" (from /monroe/config see defaults above)    


## The experiment will execute a statement similar to running curl like this
```bash
curl -o /dev/null --raw --silent --write-out "{ remote: %{remote_ip}:%{remote_port}, size: %{size_download}, speed: %{speed_download}, time: %{time_total}, time_download: %{time_starttransfer} }" --interface eth0 --max-time 100 --range 0-100 http://193.10.227.25/test/1000M.zip
```

## Docker misc usage
 * List running containers
     * ```docker ps```
 * Debug shell
     * ```docker run -i -t --entrypoint bash --net=host template```
 * Normal execution with output to stdout
     * ```docker run -i -t --net=host template```
 * Attach running container (with shell)
    * ```docker exec -i -t [container runtime name] bash```
 * Get container logs (stderr and stdout)
    * ```docker logs [container runtime name]```

## Sample output
Single line, pretty printed and added comments here for readability
```
{
    "Bytes": 30720000,
    "DataId": "jonakarl.experiment-template",
    "DataVersion": 1,
    "DownloadTime": 2.716,
    "GPSPositions": [
          {
            "Altitude": 225.0,
            "DataId": "MONROE.META.DEVICE.GPS",
            "DataVersion": 1,
            "Latitude": 59.404697,
            "Longitude": 13.581558,
            "NMEA": "$GPGGA,094832.0,5924.281896,N,01334.893500,E,1,05,1.6,225.0,M,35.0,M,,*5D\r\n",
            "SatelliteCount": 5,
            "SequenceNumber": 14,
            "Timestamp": 1465551728
          },
          {
            "DataId": "MONROE.META.DEVICE.GPS",
            "DataVersion": 1,
            "Latitude": 59.404697,
            "Longitude": 13.581558,
            "NMEA": "$GPRMC,094832.0,A,5924.281896,N,01334.893500,E,0.0,,100616,0.0,E,A*2B\r\n",
            "SequenceNumber": 15,
            "Timestamp": 1465551728
          }
    ],
    "Guid": "sha256:15979bc2e2449b0011826c2bb8668df980da88221af3fc7916cb2eba4f2296c1.0.45.15",
    "Host": "193.10.227.25",
    "Iccid": "89460850007006922138",
    "InterfaceName": "usb0",
    "NodeId": "45",
    "Operator": "Telenor SE",
    "Port": "80",
    "SequenceNumber": 1,
    "SetupTime": 0.004,
    "Speed": 11295189.0,
    "TimeStamp": 1465551458.099917,
    "TotalTime": 2.72
}
```
