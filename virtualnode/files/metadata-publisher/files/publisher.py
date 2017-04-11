#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date: June 2016
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""
A fake metadata publisher that read eventlogs from a file.

The publisher will run "forever", ie it will wrap around when the number of
recorded events are finished and start publishing the first event again.

The messages are default sent relative to the time it was recorded on
the real host. To speed up the time the TIMESCALE variable can be increased.
"""


import zmq
import random
import time
import netifaces
import sys
import json
import os
from urllib2 import urlopen

# Configuration
FILENAME = "metadata.dump"
TIMESCALE = 1.0


SEQCOUNTER = 0
INTIP = {}
# Will be the same for all interfaces
EXTERNALIP = urlopen('https://api.ipify.org/').read()

try:
    for ifname in netifaces.interfaces():
        INTIP[ifname] = (netifaces.
                         ifaddresses(ifname)[netifaces.AF_INET][0]['addr'])
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://{}:5556".format(INTIP['metadata']))
except Exception as e:
    print "Failed to create ZMQ publisher {}".format(e)
    sys.exit(1)

while True:
    try:
        # Sanity Check 1: Zero files size and existance check
        if os.stat(FILENAME).st_size == 0:
            raise Exception("Zero file size")
#        fileseqcounter = 0
        last_ts = None
        with open(FILENAME, 'r') as f:
            for line in f:
                topic, msgstr = line.split(" ", 1)
                msg = json.loads(msgstr)
    #            if fileseqcounter == 0 or
    #               jsonmsg["SequenceNumber"] < fileseqcounter:
    #                fileseqcounter = jsonmsg["SequenceNumber"]
    #            SEQCOUNTER = jsonmsg["SequenceNumber"] - fileseqcounter

                # Get the timing of the messages (semi) correct
                if last_ts is not None:
                    wait = msg["Timestamp"] - last_ts
                    if wait > 0:  # Should not not happen
                        time.sleep(wait/TIMESCALE)
                last_ts = msg["Timestamp"]

                # Make it look like a new message
                msg["SequenceNumber"] = SEQCOUNTER
                msg["Timestamp"] = time.time()

                # Update message with IP addresses from the virtual env
                if "IPAddress" in msg:
                    msg["IPAddress"] = EXTERNALIP
                if "InternalIPAddress" in msg:
                    ifname = ""
                    if "InterfaceName" in msg:  # Should always be there
                        ifname = msg["InterfaceName"]
                    if "InternalInterface" in msg:  # For modems
                        ifname = msg["InternalInterface"]
                    if ifname in INTIP:
                        msg["InternalIPAddress"] = INTIP[ifname]
                    else:
                        # We do not have this interface in the virtual node
                        continue
                zmqstr = "{} {}".format(topic, json.dumps(msg))
                # print zmqstr
                socket.send(zmqstr)
                SEQCOUNTER += 1
    except Exception as e:
        print "Failed to send ZMQ message {}".format(e)
        SEQCOUNTER += 1
        continue
