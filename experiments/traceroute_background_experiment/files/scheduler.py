#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Foivos Michelinakis
# Date: February 2017
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""
This file is used in case we want to parallelize experiments on a per interface basis.
It is launched by the main script once per interface and does the scheduling of the traceroute instances for it.
"""

import json
import os
import sys
import subprocess
import time

CONFIG_FILE = os.getcwd() + "/intermediate.json"

with open(CONFIG_FILE, "r") as fd:
    variables = json.load(fd)


# parallel execution parameters
max_proc_allowed = variables["maxNumberOfTotalTracerouteInstances"]
procs = []

for target in variables["targets"]:
    while len(procs) >= max_proc_allowed:
        # we do the checks every one second to avoid maxing out the processor for no reason
        time.sleep(1)
        for pr in procs:
            if pr.poll() == 0:
                procs.remove(pr)
    cmd = [
        "python",
        "tracerouteLauncher.py",
        variables["protocolFlag"],
        sys.argv[1],  # interface
        target
    ]
    procs.append(subprocess.Popen(cmd))

# waiting the last set of traceroutes to finish
for proc in procs:
    proc.wait()
