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

if (len(sys.argv) != 2):
    print "Usage: {} interface".format(sys.argv[0])
    print "Exiting."
    sys.exit()

interfacename=sys.argv[1]

#print "Using interface ", interfacename

# TODO: do a sanity check so we really ahev this interfae up in the system

#Listen to events only on this intrface
TOPIC = "MONROE.META.DEVICE.MODEM"

# Attach to the ZeroMQ socket as a subscriber and start listen to MONROE messages
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect('tcp://172.17.0.1:5556')
socket.setsockopt(zmq.SUBSCRIBE, TOPIC)
# End Attach

while True:
    data = socket.recv()
    
    try:
      msg = json.loads(data.split(" ", 1)[1])
      ifname = msg.get('InterfaceName')
      iccid = msg.get('ICCID')

      if ifname == interfacename and iccid is not None: 
          print iccid
          sys.exit(0)
    except Exception, ex:
      pass
