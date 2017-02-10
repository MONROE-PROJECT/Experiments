# Headlessbrowsing
This experiment evaluates the performance of different http protocols (HTTP1.1, HTTP1.1/TLS, HTTP2) 
using the headless firefox browser. The experiment uses selenium browser automation framework.
This framework allows to execute web-browsing automation tests in different browsers such as Firefox and Chrome. 
We use selenium web-driver for Firefox. For a given url, http protocol  and source network interface, the experiment launches the 
native Firefox browser to visit the url. This experiment generates HTTP ARchive (HAR) file during the download of 
a target url which assists in finding impact of different web-page features on its overall Page Load Time (PLT), afterwards.

## Input
The default input values are (can be overridden by a /monroe/config):

```
{
        "guid": "no.guid.in.config.file",  # Should be overridden by scheduler
        "url": "http://193.10.227.25/test/1000M.zip",
        "size": 3*1024,  # The maximum size in Kbytes to download
        "time": 3600,  # The maximum time in seconds for a download
        "zmqport": "tcp://172.17.0.1:5556",
        "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
        "dataversion": 1,
        "dataid": "MONROE.EXP.FIREFOX.HEADLESS.BROWSING",
        "nodeid": "fake.nodeid",
        "meta_grace": 120,  # Grace period to wait for interface metadata
        "exp_grace": 120,  # Grace period before killing experiment
        "ifup_interval_check": 5,  # Interval to check if interface is up
        "time_between_experiments": 30,
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "modeminterfacename": "InternalInterface",
        "urls": ["www.wikipedia.com"],
        "http_protocols":["h1","h1s","h2"],
        "iterations": 1,
        "allowed_interfaces": ["op0",
                               "op1",
                               "op2"],  # Interfaces to run the experiment on
        "interfaces_without_metadata": [ ]  # Manual metadata on these IF
        }
```

For example, using the above inputs (default), the experiment will download wikipedia with different combinations of 
three different http protocols and three different source interfaces each time.
So, it is possible to input required urls, http protocols, iterations, interfaces etc. during 
scheduling the experiment.

## Output
The experiment generates a single JSON file like the following

```
{  
   "DataId":"MONROE.EXP.FIREFOX.HEADLESS.BROWSING",
   "ping_min":" 55.6",
   "ping_max":"56.8",
   "NumObjects":6,
   "InterfaceName":"usb2",
   "Web load time":196,
   "PageSize":35641,
   "DataVersion":1,
   "Timestamp":1481536829.0814,
   "NWMCCMNC":22210,
   "Objects":[  
      {  
         "objectSize":1951,
         "mimeType":"image/png",
         "startedDateTime":"2016-12-12T10:00:21.293+00:00",
         "url":"https://www.wikipedia.org/portal/wikipedia.org/assets/img/Wikipedia_wordmark.png",
         "timings":{  
            "receive":1,
            "send":0,
            "connect":1,
            "dns":0,
            "blocked":0,
            "wait":60
         },
         "time":62
      },
      {  
         "objectSize":13196,
         "mimeType":"image/png",
         "startedDateTime":"2016-12-12T10:00:21.294+00:00",
         "url":"https://www.wikipedia.org/portal/wikipedia.org/assets/img/Wikipedia-logo-v2.png",
         "timings":{  
            "receive":52,
            "send":3,
            "connect":59,
            "dns":2,
            "blocked":0,
            "wait":53
         },
         "time":169
      },
      {  
         "objectSize":9425,
         "mimeType":"application/javascript",
         "startedDateTime":"2016-12-12T10:00:21.295+00:00",
         "url":"https://www.wikipedia.org/portal/wikipedia.org/assets/js/index-abc278face.js",
         "timings":{  
            "receive":3,
            "send":0,
            "connect":120,
            "dns":0,
            "blocked":0,
            "wait":65
         },
         "time":188
      },
      {  
         "objectSize":1164,
         "mimeType":"application/javascript",
         "startedDateTime":"2016-12-12T10:00:21.296+00:00",
         "url":"https://www.wikipedia.org/portal/wikipedia.org/assets/js/gt-ie9-c84bf66d33.js",
         "timings":{  
            "receive":0,
            "send":1,
            "connect":64,
            "dns":2,
            "blocked":0,
            "wait":70
         },
         "time":137
      },
      {  
         "objectSize":1590,
         "mimeType":"image/png",
         "startedDateTime":"2016-12-12T10:00:21.381+00:00",
         "url":"https://www.wikipedia.org/portal/wikipedia.org/assets/img/sprite-icons.png?27378e2bb51199321b32dd1ac3f5cd755adc21a5",
         "timings":{  
            "receive":1,
            "send":0,
            "connect":1,
            "dns":0,
            "blocked":0,
            "wait":49
         },
         "time":51
      },
      {  
         "objectSize":8315,
         "mimeType":"image/png",
         "startedDateTime":"2016-12-12T10:00:21.425+00:00",
         "url":"https://www.wikipedia.org/portal/wikipedia.org/assets/img/sprite-project-logos.png?dea6426c061216dfcba1d2d57d33f4ee315df1c2",
         "timings":{  
            "receive":2,
            "send":0,
            "connect":8,
            "dns":0,
            "blocked":0,
            "wait":54
         },
         "time":64
      }
   ],
   "IPAddress":"2.43.181.254",
   "IMSIMCCMNC":22210,
   "tracedRoutes":[  
      "192.168.96.1",
      "193.10.227.25",
      "xx.xx.xx.xx"
      .....
      "192.168.96.1"
   ],
   "InternalInterface":"op0",
   "NodeId":"41",
   "ping_exp":1,
   "Protocol":"HTTP1.1",
   "SequenceNumber":1,
   "url":"www.wikipedia.org",
   "ping_avg":"56.2",
   "InternalIPAddress":"192.168.96.123",
   "Operator":"voda IT",
   "Iccid":"8939104160000392116"
} 
```
