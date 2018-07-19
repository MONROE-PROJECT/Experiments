#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date: Sept 2015
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project
"""
    Subscribes to all MONROE.META events and print them on stdout.
"""

import zmq
import json
import time
import netifaces
import sys

CONFIGFILE = '/monroe/config'
UPDATECACHE = set()

# Default values (overwritable from the CONFIGFILE)
CONFIG = {
        "zmqport": "tcp://172.17.0.1:5556",
        "nodeid": "fake.nodeid",  # Need to overriden
        "metadata_topic": "MONROE.META",
        "verbosity": 1,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "GPSgrace": 30,  # Number of seconds to wait for GPS Info
        "OPgrace": 90  # Number of seconds to wait for GPS Info
        }


meta = []
operators = set(i for i in netifaces.interfaces() if str(i).startswith("op"))
done = False
print ("Metadata : Trying to fetch operators for {} and GPS".format(list(operators)))

try:
    with open(CONFIGFILE) as configfd:
        CONFIG.update(json.load(configfd))
except Exception as e:
    print("--> Cannot retrive config {}".format(e))
    sys.exit(1)

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect(CONFIG["zmqport"])
socket.setsockopt(zmq.SUBSCRIBE, CONFIG["metadata_topic"])

#GPS
start_time = time.time()
while (time.time() - start_time < CONFIG["GPSgrace"] and not done):
    (topic, msgdata) = socket.recv().split(' ', 1)
    msg = json.loads(msgdata)
    if topic.startswith("MONROE.META.DEVICE.GPS.GPGGA"):
        print ("--> GPS : OK \n"
               "----> Lat: {}\n"
               "----> Lon: {}\n"
               "----> Sat: {}").format(msg["Latitude"],
                                     msg["Longitude"],
                                     msg["SatelliteCount"])
        done = True

if not done:
    print ("--> GPS : No Info in {} seconds".format(CONFIG["GPSgrace"]))

#Operators
start_time = time.time()
while (time.time() - start_time < CONFIG["OPgrace"]
       and len(meta) < len(operators)):
    (topic, msgdata) = socket.recv().split(' ', 1)
    msg = json.loads(msgdata)
    if (topic.startswith("MONROE.META.DEVICE.MODEM")
        and msg["InternalInterface"] not in meta):
        ifname = msg["InternalInterface"]
        meta.append(ifname)
        print ("--> Interface {} : OK \n"
               "----> Operator: {}\n"
               "----> ICCID: {}\n"
               "----> RSSI: {}").format(ifname,
                                     msg["Operator"],
                                     msg["ICCID"],
                                     msg["RSSI"])

for i in (operators - set(meta)):
    print ("--> Interface : No info for {} in {} seconds".format(i,
                                                             CONFIG["OPgrace"]))
