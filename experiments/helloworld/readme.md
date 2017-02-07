
# Experiment
A hello world experiment that saves and print the first X metadata messages
it receives.

The default values are (can be overridden by a /monroe/config):
```
{
        "zmqport": "tcp://172.17.0.1:5556",
        "nodeid": "fake.nodeid",  # Need to overriden
        "metadata_topic": "MONROE.META",
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "nr_of_messages": 3
}
```

## Requirements

These directories and files must exist and be read/writable by the user/process
running the container:
 * /monroe/config  (supplyed by the scheduler in the nodes)
 * "resultdir" (from /monroe/config see defaults above)    

## Sample output
The experiment will produce a single line JSON object similar to these depending on the metadata received (pretty printed for readability)

```
 {
  "DataId": "MONROE.META.NODE.SENSOR",
  "DataVersion": 1,
  "SequenceNumber": 58602,
  "Timestamp": 1465888420,
  "NodeId": "9",
  "Hello": "World"
}
```
The log file will have records similar to these :
```
[2017-02-07 09:53:27.190338] Hello: Default config {
 "metadata_topic": "MONROE.META",
 "nodeid": "fake.nodeid",
 "nr_of_messages": 3,
 "resultdir": "/monroe/results/",
 "verbosity": 2,
 "zmqport": "tcp://172.17.0.1:5556"
}
[2017-02-07 09:53:27.20000] Hello: Start recoding messages with configuration {
 "metadata_topic": "MONROE.META",
 "nodeid": "fake.nodeid",
 "nr_of_messages": 3,
 "resultdir": "/monroe/results/",
 "verbosity": 2,
 "zmqport": "tcp://172.17.0.1:5556"
}
[[2017-02-07 09:53:27.30000] Recieved message 1 with topic : MONROE.META.NODE.SENSOR
{
 "DataId": "MONROE.META.NODE.SENSOR",
 "DataVersion": 1,
 "SequenceNumber": 58602,
 "Timestamp": 1465888420,
 "NodeId": "9",
 "Hello": "World"
}
. # And so on for each metadata message you receive up until the configured value of metadata messages
.
.
[2017-02-07 09:53:27.40000] Hello : Finished the experiment
```
