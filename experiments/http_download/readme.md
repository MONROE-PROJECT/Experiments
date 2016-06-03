
# Experiment
Evaluate http download speed.

The experiment will download a url (file) over http using curl.
The default values are (can be overridden by a /monroe/config):
```
{
    "allowed_interfaces": [
        "usb0",
        "usb1",
        "usb2",
        "wlan0",
        "wwan2"
    ],
    "dataid": "MONROE.EXP.HTTP.DOWNLOAD",
    "dataversion": 1,
    "exp_grace": 120,
    "guid": "no.guid.in.config.file",
    "ifup_interval_check": 5,
    "interfaces_without_metadata": [
        "eth0",
        "wlan0"
    ],
    "meta_grace": 120,
    "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
    "resultdir": "/monroe/results/",
    "size": 3071,
    "time": 3600,
    "time_between_experiments": 30,
    "url": "http://193.10.227.25/test/1000M.zip",
    "verbosity": 2,
    "zmqport": "tcp://172.17.0.1:5556"
}
```
Description of the variables in curl_experiment.py (line 31).
The download will abort when either size OR time OR actual size of the "url" is
 downloaded.

All debug/error information will be printed on stdout
 depending on the "verbosity" variable.

## Requirements

These directories and files must exist and be read/writable by the user/process
running the container.
/opt/monroe/config
"resultdir" (from /opt/monroe/config see defaults above)    


## The experiment will execute a statement similar to running curl like this
```bash
curl -o /dev/null --raw --silent --write-out "{ remote: %{remote_ip}:%{remote_port}, size: %{size_download}, speed: %{speed_download}, time: %{time_total}, time_download: %{time_starttransfer} }" --interface eth0 --max-time 100 --range 0-100 http://193.10.227.25/test/1000M.zip
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
   "DownloadTime": 49.12, # ["TotalTime"] - msg["SetupTime"]
   "SequenceNumber": 1, # Static should remove ?
   "Host": "193.10.227.25",
   "Port": "80",
   "Speed": 256.2,
   "Bytes": 101,
   "TotalTime": 50.1,
   "NodeId" : "9", # exp_config['nodeid']
   "DataId": "MONROE.EXP.HTTP.DOWNLOAD",
   "DataVersion": 1
 }
```
