#!/usr/bin/python

import sys
import subprocess

interfaceName = sys.argv[1]
IPAndMask = subprocess.check_output(['ip', 'address', 'ls', interfaceName])
for line in IPAndMask.split("\n"):
    if line.find("inet") > 0  and line.find("inet6") < 0:
        IP = line.split(" ")[5].split("/")[0]
        with open("sourceIP.txt", "w") as fd:
            fd.write(IP)


