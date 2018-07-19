# Experiment ping_traceroute
Simple experiment to run ping and traceroute with ASN lookups against several targets.

The configuration is (via /monroe/config):
```
  "ping_count" <number of pings, default 11>,
  "targets": [ "<target 1>", "<target 2>", … ]
```

The default values are (can be overridden by a /monroe/config):
```
{
  # The following value are specific to the MONROE platform
  "guid": "no.guid.in.config.file",               # Should be overridden by scheduler
  "zmqport": "tcp://172.17.0.1:5556",
  "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
  "dataversion": 2,
  "dataid": "MONROE.EXP.PINGTR",
  "nodeid": "fake.nodeid",
  "meta_grace": 120,                              # Grace period to wait for interface metadata
  "exp_grace": 3600,                               # Grace period before killing experiment
  "ifup_interval_check": 3,                       # Interval to check if interface is up
  "time_between_experiments": 0,
  "verbosity": 2,                                 # 0 = "Mute", 1=error, 2=Information, 3=verbose
  "resultdir": "/monroe/results/",
  "modeminterfacename": "InternalInterface",
  #"require_modem_metadata": {"DeviceMode": 4},   # only run if in LTE (5) or UMTS (4)
  "save_metadata_topic": "MONROE.META",
  "save_metadata_resultdir": None,                # set to a dir to enable saving of metadata
  "add_modem_metadata_to_result": False,          # set to True to add one captured modem metadata to the result
  "disabled_interfaces": ["lo",
                          "metadata",
                          "eth0"
                          ],                      # Interfaces to NOT run the experiment on
  #"enabled_interfaces": ["op0"],                 # Interfaces to run the experiment on
  "interfaces_without_metadata": ["eth0",
                                  "wlan0"],       # Manual metadata on these IF

  # These values are specific for this experiment
  "ping_count": 11,                               # number of pings
  "targets": [ "8.8.8.8" ],                       # list of targets
}
```


## Requirements

These directories and files must exist and be read/writable by the user/process
running the container.
/monroe/config
"resultdir" (from /monroe/config see defaults above)

## Sample output
The experiment will produce a single line JSON object similar to this (pretty printed and added comments here for readability)
```
{
  "DataId": "MONROE.EXP.PINGTR",
  "SequenceNumber": 1,
  "DataVersion": 2,
  "Operator": "242 14",
  "Timestamp": 1504132032.439098,
  "Guid": "sha256:531ac6ed10b1f9a686a30792f859a079f094080d9f31ac05a997211345a502ab.368631.441.1",
  "NodeId": "441",
  "Iccid": "89470715000001462725",
  "IMSIMCCMNC": 24214,
  "NWMCCMNC": 24214,
  "8.8.8.8": {
    "traceroute": {
      "target": "8.8.8.8",
      "target_ip": "8.8.8.8",
      "hops_max": "30",
      "pkt_size": "60",
      "hops": [
        {
          "hop": 1,
          "probes": [
            {
              "name": "172.18.1.1",
              "ip": "172.18.1.1",
              "asn": "AS22773",
              "rtt": 0.225,
              "annotation": null
            },
            {
              "name": "172.18.1.1",
              "ip": "172.18.1.1",
              "asn": "AS22773",
              "rtt": 0.118,
              "annotation": null
            },
            {
              "name": "172.18.1.1",
              "ip": "172.18.1.1",
              "asn": "AS22773",
              "rtt": 0.056,
              "annotation": null
            }
          ]
        },
        {
          "hop": 2,
          "probes": [
            {
              "name": null,
              "ip": null,
              "asn": null,
              "rtt": null,
              "annotation": null
            },
            {
              "name": null,
              "ip": null,
              "asn": null,
              "rtt": null,
              "annotation": null
            },
            {
              "name": null,
              "ip": null,
              "asn": null,
              "rtt": null,
              "annotation": null
            }
          ]
        },
        {
          "hop": 3,
          "probes": [
            {
              "name": "10.4.40.142",
              "ip": "10.4.40.142",
              "asn": null,
              "rtt": 36.236,
              "annotation": null
            },
            {
              "name": "10.4.40.142",
              "ip": "10.4.40.142",
              "asn": null,
              "rtt": 36.799,
              "annotation": null
            },
            {
              "name": "10.4.40.142",
              "ip": "10.4.40.142",
              "asn": null,
              "rtt": 36.668,
              "annotation": null
            }
          ]
        },
        {
          "hop": 4,
          "probes": [
            {
              "name": "10.4.44.3",
              "ip": "10.4.44.3",
              "asn": null,
              "rtt": 37.563,
              "annotation": null
            },
            {
              "name": "10.4.44.3",
              "ip": "10.4.44.3",
              "asn": null,
              "rtt": 37.436,
              "annotation": null
            },
            {
              "name": "10.4.44.3",
              "ip": "10.4.44.3",
              "asn": null,
              "rtt": 38.285,
              "annotation": null
            }
          ]
        },
        {
          "hop": 5,
          "probes": [
            {
              "name": null,
              "ip": null,
              "asn": null,
              "rtt": null,
              "annotation": null
            },
            {
              "name": null,
              "ip": null,
              "asn": null,
              "rtt": null,
              "annotation": null
            },
            {
              "name": null,
              "ip": null,
              "asn": null,
              "rtt": null,
              "annotation": null
            }
          ]
        },
        {
          "hop": 6,
          "probes": [
            {
              "name": "193.90.206.169",
              "ip": "193.90.206.169",
              "asn": "AS2116",
              "rtt": 38.688,
              "annotation": null
            },
            {
              "name": "193.90.206.169",
              "ip": "193.90.206.169",
              "asn": "AS2116",
              "rtt": 31.894,
              "annotation": null
            },
            {
              "name": "193.90.206.169",
              "ip": "193.90.206.169",
              "asn": "AS2116",
              "rtt": 31.77,
              "annotation": null
            }
          ]
        },
        {
          "hop": 7,
          "probes": [
            {
              "name": "te7-0-1.cr1.san110.as2116.net",
              "ip": "193.75.1.80",
              "asn": "AS2116",
              "rtt": 32.74,
              "annotation": null
            },
            {
              "name": "te7-0-1.cr1.san110.as2116.net",
              "ip": "193.75.1.80",
              "asn": "AS2116",
              "rtt": 32.464,
              "annotation": null
            },
            {
              "name": "te7-0-1.cr1.san110.as2116.net",
              "ip": "193.75.1.80",
              "asn": "AS2116",
              "rtt": 32.389,
              "annotation": null
            }
          ]
        },
        {
          "hop": 8,
          "probes": [
            {
              "name": "ae0.br2.stcy.as2116.net",
              "ip": "193.75.3.209",
              "asn": "AS2116",
              "rtt": 38.955,
              "annotation": null
            },
            {
              "name": "ae0.br2.stcy.as2116.net",
              "ip": "193.75.3.209",
              "asn": "AS2116",
              "rtt": 38.883,
              "annotation": null
            },
            {
              "name": "ae0.br2.stcy.as2116.net",
              "ip": "193.75.3.209",
              "asn": "AS2116",
              "rtt": 38.78,
              "annotation": null
            }
          ]
        },
        {
          "hop": 9,
          "probes": [
            {
              "name": "google-gw.br2.stcy.as2116.net",
              "ip": "193.75.10.10",
              "asn": "AS2116",
              "rtt": 38.723,
              "annotation": null
            },
            {
              "name": "google-gw.br2.stcy.as2116.net",
              "ip": "193.75.10.10",
              "asn": "AS2116",
              "rtt": 39.353,
              "annotation": null
            },
            {
              "name": "google-gw.br2.stcy.as2116.net",
              "ip": "193.75.10.10",
              "asn": "AS2116",
              "rtt": 37.21,
              "annotation": null
            }
          ]
        },
        {
          "hop": 10,
          "probes": [
            {
              "name": "216.239.40.27",
              "ip": "216.239.40.27",
              "asn": "AS15169",
              "rtt": 37.098,
              "annotation": null
            },
            {
              "name": "216.239.40.27",
              "ip": "216.239.40.27",
              "asn": "AS15169",
              "rtt": 36.132,
              "annotation": null
            },
            {
              "name": "216.239.54.181",
              "ip": "216.239.54.181",
              "asn": "AS15169",
              "rtt": 36.005,
              "annotation": null
            }
          ]
        },
        {
          "hop": 11,
          "probes": [
            {
              "name": "216.239.54.31",
              "ip": "216.239.54.31",
              "asn": "AS15169",
              "rtt": 35.824,
              "annotation": null
            },
            {
              "name": "72.14.236.133",
              "ip": "72.14.236.133",
              "asn": "AS15169",
              "rtt": 29.333,
              "annotation": null
            },
            {
              "name": "216.239.57.35",
              "ip": "216.239.57.35",
              "asn": "AS15169/AS24077",
              "rtt": 29.966,
              "annotation": null
            }
          ]
        },
        {
          "hop": 12,
          "probes": [
            {
              "name": "google-public-dns-a.google.com",
              "ip": "8.8.8.8",
              "asn": "AS15169",
              "rtt": 29.819,
              "annotation": null
            },
            {
              "name": "google-public-dns-a.google.com",
              "ip": "8.8.8.8",
              "asn": "AS15169",
              "rtt": 29.657,
              "annotation": null
            },
            {
              "name": "google-public-dns-a.google.com",
              "ip": "8.8.8.8",
              "asn": "AS15169",
              "rtt": 29.471,
              "annotation": null
            }
          ]
        }
      ],
      "time_start": 1504132042.509531,
      "time_end": 1504132052.386876,
      "raw": "traceroute to 8.8.8.8 (8.8.8.8), 30 hops max, 60 byte packets\n 1  172.18.1.1 (172.18.1.1) [AS22773]  0.225 ms  0.118 ms  0.056 ms\n 2  * * *\n 3  10.4.40.142 (10.4.40.142) [*]  36.236 ms  36.799 ms  36.668 ms\n 4  10.4.44.3 (10.4.44.3) [*]  37.563 ms  37.436 ms  38.285 ms\n 5  * * *\n 6  193.90.206.169 (193.90.206.169) [AS2116]  38.688 ms  31.894 ms  31.770 ms\n 7  te7-0-1.cr1.san110.as2116.net (193.75.1.80) [AS2116]  32.740 ms  32.464 ms  32.389 ms\n 8  ae0.br2.stcy.as2116.net (193.75.3.209) [AS2116]  38.955 ms  38.883 ms  38.780 ms\n 9  google-gw.br2.stcy.as2116.net (193.75.10.10) [AS2116]  38.723 ms  39.353 ms  37.210 ms\n10  216.239.40.27 (216.239.40.27) [AS15169]  37.098 ms  36.132 ms 216.239.54.181 (216.239.54.181) [AS15169]  36.005 ms\n11  216.239.54.31 (216.239.54.31) [AS15169]  35.824 ms 72.14.236.133 (72.14.236.133) [AS15169]  29.333 ms 216.239.57.35 (216.239.57.35) [AS15169/AS24077]  29.966 ms\n12  google-public-dns-a.google.com (8.8.8.8) [AS15169]  29.819 ms  29.657 ms  29.471 ms\n"
    },
    "ping": {
      "jitter": "6.507",
      "packet_loss": "0",
      "time_end": 1504132042.508099,
      "raw": "PING 8.8.8.8 (8.8.8.8) from 172.18.1.2 op0: 56(84) bytes of data.\n64 bytes from 8.8.8.8: icmp_seq=1 ttl=55 time=30.1 ms\n64 bytes from 8.8.8.8: icmp_seq=2 ttl=55 time=29.7 ms\n64 bytes from 8.8.8.8: icmp_seq=3 ttl=55 time=44.2 ms\n64 bytes from 8.8.8.8: icmp_seq=4 ttl=55 time=43.6 ms\n64 bytes from 8.8.8.8: icmp_seq=5 ttl=55 time=41.5 ms\n64 bytes from 8.8.8.8: icmp_seq=6 ttl=55 time=39.5 ms\n64 bytes from 8.8.8.8: icmp_seq=7 ttl=55 time=38.4 ms\n64 bytes from 8.8.8.8: icmp_seq=8 ttl=55 time=44.2 ms\n64 bytes from 8.8.8.8: icmp_seq=9 ttl=55 time=34.7 ms\n64 bytes from 8.8.8.8: icmp_seq=10 ttl=55 time=52.1 ms\n64 bytes from 8.8.8.8: icmp_seq=11 ttl=55 time=33.9 ms\n\n--- 8.8.8.8 ping statistics ---\n11 packets transmitted, 11 received, 0% packet loss, time 10014ms\nrtt min/avg/max/mdev = 29.714/39.314/52.163/6.507 ms\n",
      "host": "8.8.8.8",
      "received": "11",
      "time_start": 1504132032.444651,
      "avgping": "39.314",
      "minping": "29.714",
      "maxping": "52.163",
      "sent": "11"
    }
  }
}
```
