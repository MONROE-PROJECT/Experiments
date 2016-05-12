#!/usr/bin/python
# -*- coding: utf-8 -*-

# Authors: Stefan Alfredsson, Jonas Karlsson
# Date: Sept 2015
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

# CODENAME : Rainbow
"""Format fping ouput in json format."""
import monroe_exporter
import sys
import re
import json

# Set some variables for saving data
monroe_exporter.initalize('MONROE.EXP.PING', 1, 5.0)

if (len(sys.argv) != 2):
    print "Usage: {} InterfaceInformation [JSON]".format(sys.argv[0])
    print "Exiting."
    sys.exit()


ifinfo = json.loads(sys.argv[1])
# Remove some stuff we do not need
ifinfo.pop("DataId", None)
ifinfo.pop("SequenceNumber", None)
ifinfo.pop("DataVersion", None)
ifinfo.pop("Timestamp", None)

# These I remove since they will be obsolete very quickly
ifinfo.pop("RSSI", None)
ifinfo.pop("CID", None)
ifinfo.pop("DeviceState", None)
ifinfo.pop("RSRQ", None)
ifinfo.pop("RSRP", None)
ifinfo.pop("IPAddress", None)
ifinfo.pop("Band", None)
ifinfo.pop("DeviceMode", None)
ifinfo.pop("Frequency", None)
ifinfo.pop("LAC", None)


interface = ifinfo['InterfaceName']

print "Using {} {}".format(interface, ifinfo)

# regexp to parse fping output.
# command: fping -D -p 1000 -l 8.8.8.8
# output:
# [1442913613.489823] 8.8.8.8 : [3], 84 bytes, 5.57 ms (5.55 avg, 0% loss)
r = re.compile(r'^\[(?P<ts>[0-9]+\.[0-9]+)\] (?P<host>[^ ]+) : \[(?P<seq>[0-9]+)\], (?P<bytes>\d+) bytes, (?P<rtt>[0-9]+(?:\.[0-9]+)?) ms \(.*\)$')

# Parse incoming messages forever
line = sys.stdin.readline()

while line:
    # command: fping -D -p 1000 -l 8.8.8.8
    # output:
    # [1442913613.489823] 8.8.8.8 : [3], 84 bytes, 5.57 ms (5.55 avg, 0% loss)
    m = r.match(line)
    if m is None:
        print "Could not match regexp, exiting"
        sys.exit(1)

    # keys are defined in regexp compilation. Nice!
    exp_result = m.groupdict()
    msg = ifinfo.copy()
    msg.update({
                    'Bytes': int(exp_result['bytes']),
                    'Host': exp_result['host'],
                    'Rtt': float(exp_result['rtt']),
                    'SequenceNumber': int(exp_result['seq']),
                    'TimeStamp': float(exp_result['ts'])
                })

    monroe_exporter.save_output(msg)
    line = sys.stdin.readline()
