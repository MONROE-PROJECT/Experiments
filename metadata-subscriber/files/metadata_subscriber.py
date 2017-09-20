#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date: Sept 2015
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""Subscribes to all MONROE.META events and stores them in JSON files."""

import zmq
import json
import sys
import time
import monroe_exporter

CONFIGFILE = '/monroe/config'

UPDATECACHE = set()

# Default values (overwritable from the CONFIGFILE)
CONFIG = {
        "zmqport": "tcp://172.17.0.1:5556",
        "nodeid": "fake.nodeid",  # Need to overriden
        "metadata_topic": "MONROE.META",
        "verbosity": 1,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        }

try:
    with open(CONFIGFILE) as configfd:
        CONFIG.update(json.load(configfd))
except Exception as e:
    print("Cannot retrive config {}".format(e))
    sys.exit(1)

print ("I am running in verbosity level {}".format(CONFIG['verbosity']))

def create_socket(topic, port, verbosity):
    """Attach to a ZMQ socket as a subscriber"""
    if verbosity > 1:
        print("Trying to create a new socket on {}".format(port))
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(port)
    socket.setsockopt(zmq.SUBSCRIBE, topic)
    if verbosity > 1:
        print("New socket created listening on topic : {}".format(topic))
    return socket

# Fail hard if we cannot connect to the socket
socket = create_socket(CONFIG['metadata_topic'],
                       CONFIG['zmqport'],
                       CONFIG['verbosity'])

# Parse incomming messages forever or until a error
while True:
    # If not correct msg, skip and wait for next message
    try:
        (topic, msgdata) = socket.recv().split(' ', 1)
    except zmq.ContextTerminated:
        # The context is terminated, lets try to open another socket
        # If that fails, abort
        if CONFIG['verbosity'] > 0:
            print ("Error: ContextTerminated")
        if CONFIG['verbosity'] > 1:
            print("Sleeping 30s before trying to create a new socket")
        time.sleep(30)
        socket = create_socket(CONFIG['metadata_topic'],
                               CONFIG['zmqport'],
                               CONFIecstatic_poitrasG['verbosity'])

        continue
    except zmq.ZMQError as e:
        # Other zmq Error just log and quit
        if CONFIG['verbosity'] > 0:
            print("Error: ZMQ failed with : {}".format(e))
        raise

    # Skip all messages that belong to connectivity as they are redundant
    # as we save the modem messages.
    if topic.startswith("MONROE.META.DEVICE.CONNECTIVITY."):
        continue

    # According to specification all messages that ends with .UPDATE in the
    # topic are rebrodcasts so we skip these.
    if topic.endswith(".UPDATE"):
        if topic in UPDATECACHE:
            continue
        else:
            UPDATECACHE.add(topic)

    # If not correct JSON, skip and wait for next message
    try:
        msg = json.loads(msgdata)
        # Some zmq messages do not have nodeid information so I set it here
        msg['NodeId'] = CONFIG['nodeid']
    except:
        if CONFIG['verbosity'] > 0:
            print ("Error: Recived invalid JSON msg with topic {} from "
                   "metadata-publisher : {}").format(topic, msgdata)
        continue
    if CONFIG['verbosity'] > 2:
        print(msg)
    monroe_exporter.save_output(msg, CONFIG['resultdir'])
