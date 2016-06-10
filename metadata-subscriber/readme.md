
# Metadata subscriber
The subscriber is designed to listen to zmq messages send out by the
metadata-multicaster.

The subscriber attaches to a configurable ZeroMQ socket
(default 'tcp://172.17.0.1:5556') and listen to all messages that begins with
topic "MONROE.META" except the ones where the topic ends with ".UPDATE"
(rebroadcasts).

All messages are updated with NodeId but are otherwise saved verbatim
as a json formatted file suitable for later import in monroe db.

The default values are (can be overridden by a /monroe/config):
```
# Default values (overwritable from the CONFIGFILE)
{
        "zmqport": "tcp://172.17.0.1:5556",
        "nodeid": "fake.nodeid",  # Need to overriden
        "metadata_topic": "MONROE.META",
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
}
```

All debug/error information will be printed on stdout
depending on the "verbosity" variable.

## Requirements

These directories and files must exist and be read/writable by the user/process
running the container:
 * /monroe/config
 * "resultdir" (from /monroe/config see defaults above)

## Example usage of file
```bash
python metadata_subscriber.py
```

## Docker misc usage
 * docker ps  # list running images
 * docker exec -it [container id] bash   # attach to running container
