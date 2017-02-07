
# Experiment
Evaluate http download speed.

The experiment will download a url (file) over http using curl.
The default values are (can be overridden by a /monroe/config):
```
{
      "guid": "no.guid.in.config.file",  # Should be overridden by scheduler
      "url": "http://193.10.227.25/test/1000M.zip",
      "size": 3*1024,  # The maximum size in Kbytes to download
      "time": 3600,  # The maximum time in seconds for a download
      "zmqport": "tcp://172.17.0.1:5556",
      "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
      "dataversion": 2,
      "dataid": "MONROE.EXP.HTTP.DOWNLOAD",
      "nodeid": "fake.nodeid",
      "meta_grace": 120,  # Grace period to wait for interface metadata
      "exp_grace": 120,  # Grace period before killing experiment
      "ifup_interval_check": 5,  # Interval to check if interface is up
      "time_between_experiments": 30,
      "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
      "resultdir": "/monroe/results/",
      "modeminterfacename": "InternalInterface",
      "disabled_interfaces": ["lo",
                              "metadata",
                              "eth0",
                              "wlan0"
                              ],  # Interfaces to NOT run the experiment on
      "interfaces_without_metadata": ["eth0",
                                      "wlan0"]  # Manual metadata on these IF
}
```
The download will abort when either size OR time OR actual size of the "url" is
 downloaded.

All debug/error information will be printed on stdout
 depending on the "verbosity" variable.

## Requirements

These directories and files must exist and be read/writable by the user/process
running the container.
/opt/monroe/config
"resultdir" (from /opt/monroe/config see defaults above)    


## The experiment will produce a result equivalent to running curl with these options
```bash
curl -o /dev/null --raw --silent --write-out "{ Host: %{remote_ip}, Port :%{remote_port}, Bytes: %{size_download}, Speed: %{speed_download}, TotalTime: %{time_total}, SetupTime: %{time_starttransfer}, Url: %{url_effective} }" --interface eth0 --max-time 100 --range 0-100 http://193.10.227.25/test/1000M.zip
```

## Sample output
The experiment will produce a single line JSON object similar to this (pretty printed and added comments here for readability)
```
 {
   "Guid": "313.123213.123123.123123", # exp_config["guid"]
   "Timestamp": 23123.1212, # time.time() when curl download starts
   "Iccid": 2332323, # meta_info["ICCID"]
   "Operator": "Telia", # meta_info["Operator"]
   "DownloadTime": 49.12, # "TotalTime" - "SetupTime"
   "SequenceNumber": 1, # Static
   "Host": "193.10.227.25",
   "Port": "80",
   "Speed": 256.2,
   "Bytes": 101,
   "TotalTime": 50.1,
   "SetupTime": 3,
   "Url": "http://193.10.227.25/test/1000M.zip",
   "NodeId" : "9", # exp_config["nodeid"]
   "DataId": "MONROE.EXP.HTTP.DOWNLOAD",
   "DataVersion": 2,
   "ErrorCode": 0 # curl command error code.
 }
```
