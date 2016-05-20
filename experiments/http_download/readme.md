
# Experiment
Evaluate http download speed.

The experiment will with a configurable interval download a .zip file over http using curl.

The required parameters to run the container are
 * interface -- The local interface to bind to
 * max_size -- The maximum size in Kbytes to download (for now this is capped at 1000MB)
 * max_time -- The maximum time in seconds a single download are allowed to take
 * interval -- How long time between execution of the downloads, IF the actual download time => interval. The next file download fill start when latter is finished.

The download will abort when either Max size OR Max time OR 1000MB is downloaded.    
More information, e.g. url and options used can be found in files/run.sh and files/curl_wrapper.py


## Requirements

These directories must exist and be writable by the user/process running the container
/output/    
/etc/nodeid

## Example usage
```bash
curl -o /dev/null --raw --silent --write-out "{ remote: %{remote_ip}:%{remote_port}, size: %{size_download}, speed: %{speed_download}, time: %{time_total}, time_download: %{time_starttransfer} }" --interface eth0 --max-time 100 --range 0-100 http://speedtest.bahnhof.net/1000M.zip| python curl_formatter.py
```

## Docker misc usage

docker ps  # list running images    
docker exec -it [container id] bash   # attach to running container

## Sample output
NodeId, DataId, DataVersion will be appended to the sample output before transmission to the db (by the monroe_exporter function).
Single line printed on multiple lines for readability
```
DataId = "MONROE.EXP.HTTP.DOWNLOAD"
DataVersion = 1

 {
   "Guid": "experiment_id.scheduling_id.node_id.repetition",
   "TotalTime": 0.06,
   "InterfaceName": 'eth0',
   "TimeStamp": 1460720460.979675,
   "Bytes": 102400,
   "SetupTime": 0.027,
   "DownloadTime": 0.033,
   "Host": "213.80.98.3",
   "Speed": 1695251.0,
   "Port": "80"
 }
```

CREATE TABLE monroe_exp_http (
    NodeId         text,
 Guid           text,
    Timestamp      decimal,
 SequenceNumber bigint,
    DataId         text,
    DataVersion    int,

 Operator       text,
 Iccid          text,

 TotalTime      double,
    Bytes          int,
 SetupTime      double,
 DownloadTime   double,
    Host           text,
 Speed          double,
    Port           text,

    PRIMARY KEY (NodeId, Iccid)
);
