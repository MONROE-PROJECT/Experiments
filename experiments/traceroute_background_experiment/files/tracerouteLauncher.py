#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Foivos Michelinakis
# Date: February 2017
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project


import sys
import subprocess
import time
import os


"""
Launches the traceroute binary to the specified target and then calls the parser.
"""

CURRENT_DIR = os.getcwd() + "/"
SCRIPT_DIR = '/opt/traceroute/'

cmd = [
    "traceroute",
    sys.argv[1],
    "-i",
    sys.argv[2],
    sys.argv[3]
]

# in case the protocol flag is empty we remove it to
# avoid issues with subprocess.check_output
while 'default' in cmd:
    cmd.remove('default')

# doing the measurement
start = int(time.time())
output = subprocess.check_output(cmd)
end = int(time.time())


# saving the output to a file.
filename = "tracerouteOutput_" + str(start) + "_" + str(end) + "_" + \
            sys.argv[2] + "_" + sys.argv[1] + "_" + \
            sys.argv[3] + ".txt"
with open(CURRENT_DIR + filename, "w") as outputFile:
    outputFile.write(output)

# parsing the result
cmd = [
    "python",
    SCRIPT_DIR + "outputParser.py",
    filename
]

subprocess.call(cmd)


