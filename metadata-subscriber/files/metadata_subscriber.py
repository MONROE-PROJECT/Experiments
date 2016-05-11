#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date: Sept 2015
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""Subscribes to all MONROE.META events and stores them in JSON files."""

import zmq
import json
import syslog
import monroe_exporter

TOPIC = 'MONROE.META'

# Attach to the ZeroMQ socket as a subscriber and start listen to
# MONROE messages
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect('tcp://172.17.0.1:5556')
socket.setsockopt(zmq.SUBSCRIBE, TOPIC)
# End Attach

# Parse incomming messages forever
while True:
    # If not correct msg, skip and wait for next message
    try:
        (topic, msgdata) = socket.recv().split(' ', 1)
    except:
        syslog.syslog(syslog.LOG_ERROR, "Invalid zmq msg")
        continue

    # According to specification all messages with UPDATE in the topic are
    # rebrodcasts so we skip these.
    if ".UPDATE" in topic:
        continue

    # If not correct JSON, skip and wait for next message
    try:
        msg = json.loads(msgdata)
    except:
        syslog.syslog(syslog.LOG_ERRROR,
                      ("Recived invalid JSON msg with topic {} from "
                       "metadata-multicaster : {}").format(topic, msg))
        continue

    monroe_exporter.save_output(msg, msg['DataId'], msg['DataVersion'])
