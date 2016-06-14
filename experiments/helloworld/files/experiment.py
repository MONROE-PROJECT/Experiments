#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date: June 2016
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

""" Dumps the three first metadata events both in files and on stdout. """
import zmq
import json
import monroe_exporter
from datetime import datetime

CONFIGFILE = '/monroe/config'

# Default values (overwritable from the CONFIGFILE)
CONFIG = {
        "zmqport": "tcp://172.17.0.1:5556",
        "nodeid": "fake.nodeid",  # Need to overriden
        "metadata_topic": "MONROE.META",
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "nr_of_messages": 3
        }

print ("[{}] Hello: Default config {}").format(datetime.now(),
                                               json.dumps(CONFIG,
                                                          sort_keys=True,
                                                          indent=2))

try:
    with open(CONFIGFILE) as configfd:
        CONFIG.update(json.load(configfd))
        # Attach to the ZeroMQ socket as a subscriber and start listen to
        # MONROE messages
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect(CONFIG['zmqport'])
        socket.setsockopt(zmq.SUBSCRIBE, CONFIG['metadata_topic'])
        # End Attach

        # Parse X first messages
        if CONFIG['verbosity'] > 1:
            print ("[{}] Hello: Start recoding messages "
                   "with configuration {}").format(datetime.now(),
                                                   json.dumps(CONFIG,
                                                              sort_keys=True,
                                                              indent=2))
        for x in xrange(CONFIG["nr_of_messages"]):

            (topic, msgdata) = socket.recv().split(' ', 1)

            msg = json.loads(msgdata)
            if CONFIG['verbosity'] > 1:
                    print ("[{}] Recieved message {}"
                           " with topic : {}\n "
                           "{}").format(datetime.now(), x,
                                        topic,
                                        json.dumps(msg,
                                                   sort_keys=True,
                                                   indent=2))

            # Add some fields to the message
            msg['NodeId'] = CONFIG['nodeid']
            msg['Hello'] = "World"

            # Save the message in the file with updated fields
            monroe_exporter.save_output(msg, CONFIG['resultdir'])

except Exception as e:
    print ("[{}] Cannot retrive config {} "
           "running outside a monre node?"
           ", skip trying to get metdata").format(datetime.now(), e)

if CONFIG['verbosity'] > 1:
    print "[{}] Hello : Finished the experiment".format(datetime.now())
