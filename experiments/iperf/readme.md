
# Experiment
A iperf experiment design to run on a virtual monroe node.

### Notes:
* The results for protocol = udp is only stable with iperf3
* Allowed iperfversions are 2 or 3
* iperfversion corresponds to DataVersion in the outputfile.  

The default values are (can be overridden by /monroe/config):
```
{
        "zmqport": "tcp://172.17.0.1:5556",
        "guid": "fake.guid",  # Need to be overriden
        "nodeid": "virtual",
        "metadata_topic": "MONROE.META",
        "dataid": "5GENESIS.EXP.IPERF",
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "server": "130.243.27.222",
        "protocol": "tcp",
        "interfaces": [ "eth0" ],
        "iperfversion": 3 # 2 = "iperf", 3=iperf3
}
```

## Requirements

These directories and files must exist and be read/writable by the user/process
running the container:
 * /monroe/config  (supplyed by the scheduler in the nodes)
 * "resultdir" (from /monroe/config see defaults above)    

## Sample output
The experiment will produce a JSON object (file) per interface (and ip) configured 
in input "interfaces" with a filename similar to this 
5GENESIS.EXP.IPERF.2.tcp_7_1551446332.88_eth0_172.18.3.2.json

### "Iperf2"
```
 {
  "DataId": "5GENESIS.EXP.IPERF",
  "Protocol": "tcp",
  "DataVersion": 2,
  "Interface": "eth0",
  "Timestamp": 1551446332.883225,
  "Guid": "sha256:a4b55ff5a8893c2e267394fd6481a7908e0a7dd9a48d6a29458104b411712ff9.test-iperf2.7.1",
  "NodeId": "7",
  "Results": {
    "transferID": "3",
    "transferred_bytes": "1012662272",
    "source_port": "52977",
    "timestamp": "20190301131852.883",
    "destination_address": "192.168.100.13",
    "interval": "0.0-10.0",
    "source_address": "172.18.3.2",
    "destination_port": "5001",
    "bits_per_second": "809884422"
  }
}
```

### "iperf3"
´´´
{
  "DataId": "5GENESIS.EXP.IPERF",
  "Protocol": "tcp",
  "DataVersion": 3,
  "Interface": "eth0",
  "Timestamp": 1551446053.787472,
  "Guid": "sha256:a4b55ff5a8893c2e267394fd6481a7908e0a7dd9a48d6a29458104b411712ff9.test-iperf3.7.1",
  "NodeId": "7",
  "Results": {
    "start": {
      "connecting_to": {
        "host": "192.168.100.13",
        "port": 5201
      },
      "timestamp": {
        "timesecs": 1551446043,
        "time": "Fri, 01 Mar 2019 13:14:03 GMT"
      },
      "test_start": {
        "protocol": "TCP",
        "num_streams": 1,
        "omit": 0,
        "bytes": 0,
        "blksize": 131072,
        "duration": 10,
        "blocks": 0,
        "reverse": 0
      },
      "system_info": "Linux 90aa79fc96fb 4.9.0-8-amd64 #1 SMP Debian 4.9.110-3+deb9u6 (2018-10-08) x86_64",
      "version": "iperf 3.1.3",
      "connected": [
        {
          "local_host": "172.18.3.2",
          "remote_port": 5201,
          "remote_host": "192.168.100.13",
          "socket": 4,
          "local_port": 36717
        }
      ],
      "cookie": "90aa79fc96fb.1551446043.597668.7500f",
      "tcp_mss_default": 1398
    },
    "intervals": [
      {
        "sum": {
          "end": 1.000105,
          "seconds": 1.000105,
          "bits_per_second": 817688301.083527,
          "bytes": 102221760,
          "start": 0,
          "retransmits": 2,
          "omitted": false
        },
        "streams": [
          {
            "end": 1.000105,
            "socket": 4,
            "rtt": 3960,
            "seconds": 1.000105,
            "bits_per_second": 817688301.083527,
            "bytes": 102221760,
            "start": 0,
            "retransmits": 2,
            "omitted": false,
            "snd_cwnd": 426390
          }
        ]
      },
      {
        "sum": {
          "end": 2.000106,
          "seconds": 1.000001,
          "bits_per_second": 819540175.03198,
          "bytes": 102442644,
          "start": 1.000105,
          "retransmits": 0,
          "omitted": false
        },
        "streams": [
          {
            "end": 2.000106,
            "socket": 4,
            "rtt": 5492,
            "seconds": 1.000001,
            "bits_per_second": 819540175.03198,
            "bytes": 102442644,
            "start": 1.000105,
            "retransmits": 0,
            "omitted": false,
            "snd_cwnd": 575976
          }
        ]
      },
      {
        "sum": {
          "end": 3.00013,
          "seconds": 1.000024,
          "bits_per_second": 816434902.675058,
          "bytes": 102056796,
          "start": 2.000106,
          "retransmits": 2,
          "omitted": false
        },
        "streams": [
          {
            "end": 3.00013,
            "socket": 4,
            "rtt": 6494,
            "seconds": 1.000024,
            "bits_per_second": 816434902.675058,
            "bytes": 102056796,
            "start": 2.000106,
            "retransmits": 2,
            "omitted": false,
            "snd_cwnd": 687816
          }
        ]
      },
      {
        "sum": {
          "end": 4.000117,
          "seconds": 0.999987,
          "bits_per_second": 807718879.060123,
          "bytes": 100963560,
          "start": 3.00013,
          "retransmits": 1,
          "omitted": false
        },
        "streams": [
          {
            "end": 4.000117,
            "socket": 4,
            "rtt": 7389,
            "seconds": 0.999987,
            "bits_per_second": 807718879.060123,
            "bytes": 100963560,
            "start": 3.00013,
            "retransmits": 1,
            "omitted": false,
            "snd_cwnd": 787074
          }
        ]
      },
      {
        "sum": {
          "end": 5.000173,
          "seconds": 1.000056,
          "bits_per_second": 807663227.948988,
          "bytes": 100963560,
          "start": 4.000117,
          "retransmits": 0,
          "omitted": false
        },
        "streams": [
          {
            "end": 5.000173,
            "socket": 4,
            "rtt": 8568,
            "seconds": 1.000056,
            "bits_per_second": 807663227.948988,
            "bytes": 100963560,
            "start": 4.000117,
            "retransmits": 0,
            "omitted": false,
            "snd_cwnd": 877944
          }
        ]
      },
      {
        "sum": {
          "end": 6.00015,
          "seconds": 0.999977,
          "bits_per_second": 808756111.780852,
          "bytes": 101092176,
          "start": 5.000173,
          "retransmits": 0,
          "omitted": false
        },
        "streams": [
          {
            "end": 6.00015,
            "socket": 4,
            "rtt": 9689,
            "seconds": 0.999977,
            "bits_per_second": 808756111.780852,
            "bytes": 101092176,
            "start": 5.000173,
            "retransmits": 0,
            "omitted": false,
            "snd_cwnd": 959028
          }
        ]
      },
      {
        "sum": {
          "end": 7.000167,
          "seconds": 1.000017,
          "bits_per_second": 812324711.522149,
          "bytes": 101542332,
          "start": 6.00015,
          "retransmits": 0,
          "omitted": false
        },
        "streams": [
          {
            "end": 7.000167,
            "socket": 4,
            "rtt": 10018,
            "seconds": 1.000017,
            "bits_per_second": 812324711.522149,
            "bytes": 101542332,
            "start": 6.00015,
            "retransmits": 0,
            "omitted": false,
            "snd_cwnd": 1034520
          }
        ]
      },
      {
        "sum": {
          "end": 8.000122,
          "seconds": 0.999955,
          "bits_per_second": 809288339.432058,
          "bytes": 101156484,
          "start": 7.000167,
          "retransmits": 0,
          "omitted": false
        },
        "streams": [
          {
            "end": 8.000122,
            "socket": 4,
            "rtt": 10836,
            "seconds": 0.999955,
            "bits_per_second": 809288339.432058,
            "bytes": 101156484,
            "start": 7.000167,
            "retransmits": 0,
            "omitted": false,
            "snd_cwnd": 1105818
          }
        ]
      },
      {
        "sum": {
          "end": 9.000162,
          "seconds": 1.00004,
          "bits_per_second": 811791676.23538,
          "bytes": 101478024,
          "start": 8.000122,
          "retransmits": 0,
          "omitted": false
        },
        "streams": [
          {
            "end": 9.000162,
            "socket": 4,
            "rtt": 11213,
            "seconds": 1.00004,
            "bits_per_second": 811791676.23538,
            "bytes": 101478024,
            "start": 8.000122,
            "retransmits": 0,
            "omitted": false,
            "snd_cwnd": 1171524
          }
        ]
      },
      {
        "sum": {
          "end": 10.000223,
          "seconds": 1.000061,
          "bits_per_second": 816107503.326209,
          "bytes": 102019640,
          "start": 9.000162,
          "retransmits": 0,
          "omitted": false
        },
        "streams": [
          {
            "end": 10.000223,
            "socket": 4,
            "rtt": 11932,
            "seconds": 1.000061,
            "bits_per_second": 816107503.326209,
            "bytes": 102019640,
            "start": 9.000162,
            "retransmits": 0,
            "omitted": false,
            "snd_cwnd": 1234434
          }
        ]
      }
    ],
    "end": {
      "sum_received": {
        "seconds": 10.000223,
        "start": 0,
        "bytes": 1013134794,
        "end": 10.000223,
        "bits_per_second": 810489767.650944
      },
      "streams": [
        {
          "sender": {
            "end": 10.000223,
            "socket": 4,
            "max_rtt": 11932,
            "seconds": 10.000223,
            "bits_per_second": 812731463.278758,
            "bytes": 1015936976,
            "max_snd_cwnd": 1234434,
            "min_rtt": 3960,
            "start": 0,
            "retransmits": 5,
            "mean_rtt": 8559
          },
          "receiver": {
            "end": 10.000223,
            "socket": 4,
            "seconds": 10.000223,
            "bits_per_second": 810489767.650944,
            "bytes": 1013134794,
            "start": 0
          }
        }
      ],
      "cpu_utilization_percent": {
        "remote_user": 9.5e-05,
        "remote_system": 0.000918,
        "remote_total": 0.001014,
        "host_system": 1.269514,
        "host_total": 1.376223,
        "host_user": 0.119017
      },
      "sum_sent": {
        "end": 10.000223,
        "seconds": 10.000223,
        "bits_per_second": 812731463.278758,
        "bytes": 1015936976,
        "start": 0,
        "retransmits": 5
      }
    }
  }
}
´´´

