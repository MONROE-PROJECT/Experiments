#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Foivos Michelinakis
# Date: February 2017
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project


"""
This file controls the background traceroute experiment.
It is expected to run periodically at all nodes and its results are stored
in the MONROE database.

The parameters of this experiment will be provided as "Additional options".
"Additional options" are passed to the experiment when it is scheduled at the experiment
scheduling web interface (https://www.monroe-system.eu/NewExperiment.html).
If "Additional options" fails to load a set of default parameters is used instead.

An example "Additional options" JSON string that can be used with this container is:

"internal": 1, "basedir": "/traceroute", "interfaces": ["op0", "op1", "op2"], "targets": ["www.ntua.gr", "www.uc3m.es", "Google.com", "Facebook.com", "Youtube.com", "Baidu.com", "Yahoo.com", "Amazon.com", "Wikipedia.org", "audio-ec.spotify.com", "mme.whatsapp.net", "sync.liverail.com", "ds.serving-sys.com", "instagramstatic-a.akamaihd.net"], "maxNumberOfTotalTracerouteInstances": 5, "executionMode": "parallel"
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
SCRIPT_DIR = '/opt/traceroute/'
containerTimestamp = int(time.time())

# default parameters
nodeId = "0"
interfaces = ["op0", "op1", "op2"]
targets = ["www.uc3m.es"]
protocol = "default"  # "default", "udp", "tcp", "icmp"
executionMode = "serially"  # serially, serialPerInterface, parallel
usingDefaults = False  # in case a parameter is not specified / broken
maxNumberOfTotalTracerouteInstances = 5
DataId = "MONROE.EXP.SIMPLE.TRACEROUTE"
DataVersion = 1

protocolFlagMapping = {
    "default": 'default',
    "udp": '-U',
    "tcp": '-T',
    "icmp": '-I'
}

try:
    with open(CONFIG_FILE, "r") as fd:
        configurationParameters = json.load(fd)
except Exception as e:
    print "Cannot retrive CONFIG_FILE {}".format(e)
    print "Using default parameters......."
    configurationParameters = {}
    usingDefaults = True

nodeId = str(configurationParameters.get("nodeid", nodeId))
interfaces = configurationParameters.get("interfaces", interfaces)
targets = configurationParameters.get("targets", targets)
protocol = configurationParameters.get("protocol", protocol)
executionMode = configurationParameters.get("executionMode", executionMode)
maxNumberOfTotalTracerouteInstances = configurationParameters.get(
    "maxNumberOfTotalTracerouteInstances", maxNumberOfTotalTracerouteInstances
    )
DataId = configurationParameters.get("DataId", DataId)
DataVersion = configurationParameters.get("DataVersion", DataVersion)

if protocol in protocolFlagMapping.keys():
    protocolFlag = protocolFlagMapping[protocol]
else:
    protocolFlag = 'default'
    usingDefaults = True

variables = {
            "usingDefaults": usingDefaults,
            "maxNumberOfTotalTracerouteInstances": maxNumberOfTotalTracerouteInstances,
            "protocolFlag": protocolFlag,
            "targets": targets,
            "nodeId": nodeId,
            "containerTimestamp": containerTimestamp,
            "DataVersion": DataVersion,
            "DataId": DataId
        }

INTERMEDIATE_CONFIG_FILE = os.getcwd() + "/intermediate.json"
with open(INTERMEDIATE_CONFIG_FILE, 'wb') as fp:
    json.dump(variables, fp)

if executionMode == "serially":
    for interface in interfaces:
        for target in targets:
            cmd = [
                "python",
                SCRIPT_DIR + "tracerouteLauncher.py",
                protocolFlag,
                interface,
                target
            ]
            proc = subprocess.Popen(cmd)
            proc.wait()
elif executionMode == "serialPerInterface":
    interfacesProcesses = []
    for interface in interfaces:
        commandList = [
            "python",
            SCRIPT_DIR  + "scheduler.py",
            interface
            ]
        interfacesProcesses.append(subprocess.Popen(commandList))
    for proc in interfacesProcesses:
        proc.wait()
elif executionMode == "parallel":
    max_proc_allowed = maxNumberOfTotalTracerouteInstances
    procs = []
    for target in targets:
        for interface in interfaces:
            while len(procs) >= max_proc_allowed:
                # we do the checks every one second to avoid maxing out the processor for no reason
                time.sleep(1)
                for pr in procs:
                    # A None value indicates that the process hasn’t terminated yet.
                    if pr.poll() != None:
                        procs.remove(pr)
            cmd = [
                "python",
                SCRIPT_DIR + "tracerouteLauncher.py",
                protocolFlag,
                interface,
                target
            ]
            procs.append(subprocess.Popen(cmd))
    # waiting the last set of traceroutes to finish
    for proc in procs:
        proc.wait()
else:
    print "Unable to define executionMode. Exitting.....\n"
    sys.exit(1)

"""
# since all the traceroutes have finished and all the results are in json format (the resutls
# files have the ending ".parsed"), we copy them to the RESULTS_DIR, so that they can be 
# send to the database
for resultFile in [fileName for fileName in os.listdir(CURRENT_DIR) if fileName.endswith(".parsed")]:
    # we do not copy directly the files in order to avoid possivble corruption during the
    # automatic export
    shutil.copy2(CURRENT_DIR + resultFile, RESULTS_DIR + resultFile + ".tmp")
    shutil.move(RESULTS_DIR + resultFile + ".tmp", RESULTS_DIR + resultFile.replace(".parsed", ".json"))
"""
# we allow some time for the exporter to send the files. When this script finishes the
# experiment stops right away, so if a file has not been uploaded it is lost.
time.sleep(30)
