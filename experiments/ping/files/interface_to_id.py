#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date: Sept 2015
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

# CODENAME : Rainbow

import zmq
import json
import sys

if (len(sys.argv) != 3):
    print "Usage: {} interface timeout(integer)".format(sys.argv[0])
    print "Exiting."
    sys.exit()

interfacename=sys.argv[1]
timeout=int(sys.argv[2])

print "Using interface ", interfacename
print "Waiting max ", timeout

# TODO: do a sanity check so we really ahev this interfae up in the system

#Listen to events only on this intrface
TOPIC = "MONROE.META.DEVICE.MODEM.{}".format(interfacename)

# Attach to the ZeroMQ socket as a subscriber and start listen to MONROE messages
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect('tcp://localhost:5557')
socket.setsockopt(zmq.SUBSCRIBE, TOPIC)
# End Attach

# Wait for the first message 
if (([socket], [], []) != zmq.select([socket], [], [], timeout)):
    quit()

(topic, msgdata) = socket.recv_multipart()

# The msg should conatin the intrface_id field in teh body (pre requist)    
msg = json.loads(msgdata)
body = msg['Data']

print body['interface_id']
