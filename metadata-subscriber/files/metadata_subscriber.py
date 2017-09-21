#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date: Sept 2015
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""
    Subscribes to all MONROE.META events and stores them in JSON files.

    This is the workaround version where I am using pollers to overcome
    a possible hanged socket.
"""
DEBUG = False

import zmq
import json
import sys
if not DEBUG:
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
        "socketwait": 60  # Number of seconds to wait for data on the socket
        }

if not DEBUG:
    try:
        with open(CONFIGFILE) as configfd:
            CONFIG.update(json.load(configfd))
    except Exception as e:
        print("Cannot retrive config {}".format(e))
        sys.exit(1)
else:
    CONFIG['zmqport'] = "tcp://localhost:5556"
    CONFIG['metadata_topic'] = ""
    CONFIG['verbosity'] = 3
    CONFIG['socketwait'] = 10

print (("I am running in verbosity level {} "
        "and are waiting {}s on the socket").format(CONFIG['verbosity'],
                                                    CONFIG['socketwait']))

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

# Initialize poll set
poller = zmq.Poller()
poller.register(socket, zmq.POLLIN)


# Parse incomming messages forever or until a error
while True:
    socks = dict(poller.poll(CONFIG['socketwait']*1000))
    if not (socket in socks and socks[socket] == zmq.POLLIN):
        # Something strange happend lets try to reconnect and try again
        if CONFIG['verbosity'] > 0:
            print (("Error: We did not get any data for "
                    "{} seconds").format(CONFIG['socketwait']))
        socket = create_socket(CONFIG['metadata_topic'],
                               CONFIG['zmqport'],
                               CONFIG['verbosity'])
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)
        continue

    # We should have a good working socket
    try:
        (topic, msgdata) = socket.recv(zmq.DONTWAIT).split(' ', 1)
    except zmq.ContextTerminated:
        # The context is terminated, lets try to open another socket
        # If that fails, abort
        if CONFIG['verbosity'] > 0:
            print ("Error: ContextTerminated")
        socket = create_socket(CONFIG['metadata_topic'],
                               CONFIG['zmqport'],
                               CONFIG['verbosity'])
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)
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
        if not DEBUG:
            msg = json.loads(msgdata)
            # Some zmq messages do not have nodeid information so I set it here
            msg['NodeId'] = CONFIG['nodeid']
        else:
            msg = msgdata
    except:
        if CONFIG['verbosity'] > 0:
            print ("Error: Recived invalid JSON msg with topic {} from "
                   "metadata-publisher : {}").format(topic, msgdata)
        continue
    if CONFIG['verbosity'] > 2:
        print(msg)
    if not DEBUG:
        monroe_exporter.save_output(msg, CONFIG['resultdir'])
