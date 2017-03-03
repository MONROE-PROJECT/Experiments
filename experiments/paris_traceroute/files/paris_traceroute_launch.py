#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Foivos Michelinakis
# Date: February 2017
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project


"""
Example experiment to show case how to use paris-traceroute within a MONROE container.
It uses a modified paris-traceroute binary, which is able to function properly within
a MONROE container and is included in the base image of MONROE.
https://github.com/FoivosMichelinakis/paris-traceroute-monroe-project

The parameters of this experiment will be provided as "Additional options".
"Additional options" are passed to the experiment when it is scheduled at the experiment
scheduling web interface (https://www.monroe-system.eu/NewExperiment.html).

An example "Additional options" JSON string that can be used with this container is:
"interfaces": ["op1", "op2"], "targets": ["8.8.8.8", "www.uc3m.es"], "traceAlgos": ["exh"], "protocol": "udp"
"""

import json
import sys
import time
import subprocess
import os
import shutil

CONFIG_FILE = '/monroe/config'
RESULTS_DIR = "/monroe/results/"


CURRENT_DIR = os.getcwd() + "/"

try:
    with open(CONFIG_FILE, "r") as fd:
        configurationParameters = json.load(fd)
        nodeId = str(configurationParameters["nodeid"])
        interfaces = configurationParameters["interfaces"]
        targets = configurationParameters["targets"]
        traceAlgos = configurationParameters["traceAlgos"]
        protocol = configurationParameters["protocol"]
except Exception as e:
    print "Cannot retrive CONFIG_FILE {}".format(e)
    sys.exit(1)

for interface in interfaces:
    for target in targets:
        for traceAlgo in traceAlgos:
            start = "%.6f" % time.time()
            if traceAlgo == "exh":
                cmd = ["paris-traceroute",
                       "-O",
                       interface,
                       "-n",
                       "-a",
                       "exh",
                       "-p",
                       protocol,
                       target]
            elif traceAlgo == "simple":
                cmd = ["paris-traceroute",
                       "-O",
                       interface,
                       "-p",
                       protocol,
                       target]
            else:
                print "Unknown traceroute type: {}\nIgnoring........".format(traceAlgo)
                continue
            output = subprocess.check_output(cmd)
            end = "%.6f" % time.time()
            filename = "ParisTracerouteOutput_" + str(start) + "_" + str(end) + "_" + \
                       interface + "_" + protocol + "_" + traceAlgo + "_" + \
                       target + "_" + nodeId + ".txt"
            with open(CURRENT_DIR + filename, "w") as outputFile:
                outputFile.write(output)

for resultFile in [fileName for fileName in os.listdir(CURRENT_DIR) if fileName.endswith(".txt")]:
    # we do not copy directly the files in order to avoid possivble corruption during the
    # automatic export
    shutil.copy2(CURRENT_DIR + resultFile, RESULTS_DIR + resultFile + ".tmp")
    shutil.move(RESULTS_DIR + resultFile + ".tmp", RESULTS_DIR + resultFile)

# we allow some time for the exporter to send the files. When this script finishes the
# experiment stops right away, so if a file has not been uploaded it is lost.
time.sleep(30)
