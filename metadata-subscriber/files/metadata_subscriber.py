#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date: Sept 2015
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""Subscribes to all MONROE.META events and stores them in JSON files."""

import zmq
import json
import monroe_exporter

CONFIGFILE = '/monroe/config'

# Default values (overwritable from the CONFIGFILE)
CONFIG = {
        "zmqport": "tcp://172.17.0.1:5556",
        "nodeid": "fake.nodeid",  # Need to overriden
        "metadata_topic": "MONROE.META",
        "verbosity": 1,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        }
# Attach to the ZeroMQ socket as a subscriber and start listen to
# MONROE messages
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect(CONFIG['zmqport'])
socket.setsockopt(zmq.SUBSCRIBE, CONFIG['metadata_topic'])
# End Attach

# Parse incomming messages forever
while True:
    # If not correct msg, skip and wait for next message
    try:
        (topic, msgdata) = socket.recv().split(' ', 1)
    except:
        if CONFIG['verbosity'] > 0:
            print ("Error: Invalid zmq msg")
        continue

    # According to specification all messages with UPDATE in the topic are
    # rebrodcasts so we skip these.
    if ".UPDATE" in topic:
        continue

    # If not correct JSON, skip and wait for next message
    try:
        msg = json.loads(msgdata)
        # Some zmq messages do not have nodeid information so I set it here
        msg['NodeId'] = CONFIG['nodeid']
    except:
        if CONFIG['verbosity'] > 0:
            print ("Error: Recived invalid JSON msg with topic {} from "
                   "metadata-multicaster : {}").format(topic, msg)
        continue
    if CONFIG['verbosity'] > 2:
        print msg
    monroe_exporter.save_output(msg, CONFIG['resultdir'])
