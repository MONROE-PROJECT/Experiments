
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
Depends on metadata received (pretty printed for readability)
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
