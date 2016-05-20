#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date: May 2016
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

import zmq
import json
import sys
import syslog
from multiprocessing import Process, Manager
import subprocess
import netifaces
import re
import time
import monroe_exporter

# Configuration
TOPIC = 'MONROE.META.DEVICE.MODEM'
CONFIGFILE = '/monroe/config'
ZMQPORT = 'tcp://172.17.0.1:5556'
IFUP_INTERVAL_CHECK = 5  # Check if up with this interval (if it is down)
IF_META_GRACE = 60  # The grace period to wait for IF metadata
DATAVERSION = 1
DATATYPE = 'MONROE.EXP.PING'
EXPORT_INTERVAL = 5.0


def run_exp(meta_info, guid):
    # Set some variables for saving data
    monroe_exporter.initalize(DATATYPE, DATAVERSION, EXPORT_INTERVAL)

    ifname = meta_info['InterfaceName']
    cmd = ["fping",
           "-I", ifname,
           "-D",
           "-p", "1000",
           "-l", "8.8.8.8"]
    # Regexp to parse fping ouput from command
    r = re.compile(r'^\[(?P<ts>[0-9]+\.[0-9]+)\] (?P<host>[^ ]+) : \[(?P<seq>[0-9]+)\], (?P<bytes>\d+) bytes, (?P<rtt>[0-9]+(?:\.[0-9]+)?) ms \(.*\)$')

    popen = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             bufsize=1)
    stdout_lines = iter(popen.stdout.readline, "")
    # This is the inner loop where we wait for output from fping
    # This will run until we get a interface hickup
    for line in stdout_lines:
        m = r.match(line)
        if m is None:
            print "Could not match regexp, exiting"
            sys.exit(1)

        # keys are defined in regexp compilation. Nice!
        exp_result = m.groupdict()
        msg = {
                        'Guid': guid,
                        'Bytes': int(exp_result['bytes']),
                        'Host': exp_result['host'],
                        'Rtt': float(exp_result['rtt']),
                        'SequenceNumber': int(exp_result['seq']),
                        'TimeStamp': float(exp_result['ts']),
                        "Iccid": meta_info["ICCID"],
                        "Operator": meta_info["Operator"]
               }

        monroe_exporter.save_output(msg)
        # print msg

    # Cleanup
    popen.stdout.close()
    returncode = popen.wait()
    if returncode != 0:
        raise subprocess.CalledProcessError(returncode, command)


def metadata(meta_ifinfo, ifname, guid, topic, port):
    # Attach to the ZeroMQ socket as a subscriber
    # and start listen to MONROE messages
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(port)
    socket.setsockopt(zmq.SUBSCRIBE, topic)
    # End Attach
    while True:
        data = socket.recv()
        try:
            ifinfo = json.loads(data.split(" ", 1)[1])
            if ifinfo['InterfaceName'] == ifname:
                # Cannot do a simple copy here as meta_info is a Manager dict
                for key, value in ifinfo.iteritems():
                    meta_ifinfo[key] = value
        except Exception as e:
            log_str = ("Cannot get modem metadata in ping container {}"
                       ", {}").format(e, guid)

            # Everything that is printed in the container goes to syslog
            print log_str
            # if we want to use syslog directly instead
            # syslog.syslog(syslog.LOG_ERR, log_str)
            pass


# Helper functions
def check_if(ifname):
    return (ifname in netifaces.interfaces() and
            netifaces.AF_INET in netifaces.ifaddresses(ifname))


def check_meta(info, graceperiod):
    return ("InterfaceName" in info and
            "Operator" in info and
            "Timestamp" in info and
            time.time() - info["Timestamp"] < graceperiod)


def create_meta_process(ifname, guid, topic, port):
    meta_info = Manager().dict()
    process = Process(target=metadata,
                      args=(meta_info, ifname, guid, topic, port, ))
    process.daemon = True
    return (meta_info, process)


def create_exp_process(meta_info, guid):
    process = Process(target=run_exp, args=(meta_info, guid, ))
    process.daemon = True
    return process


if __name__ == '__main__':
    expconfig = {}
    ifname = ""
    # Try to get the experiment config as provided by the scheduler
    try:
        with open(CONFIGFILE) as configfd:
            expconfig = json.load(configfd)
            ifname = expconfig['interfacename']
            guid = expconfig['guid']
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, "Cannot retrive expconfig {}".format(e))
        raise e

    # Create a process for getting the metadata
    # (could have used a thread as well but this is true multiprocessing)
    meta_info, meta_process = create_meta_process(ifname,
                                                  guid,
                                                  TOPIC,
                                                  ZMQPORT)
    meta_process.start()

    # Creat a experiment script
    exp_process = exp_process = create_exp_process(meta_info,
                                                   guid)

    # Control the processes
    while True:
        # If meta dies recreate and start it (should not happen)
        if not meta_process.is_alive():
            # This is serious as we will not receive uptodate information
            if exp_process.is_alive():  # Clean up the exp_thread
                exp.terminate()

            # The dict may have been corrupt so recreate that one
            meta_info, meta_process = create_meta_process(ifname,
                                                          guid,
                                                          TOPIC,
                                                          ZMQPORT)
            meta_process.start()
            exp_process = create_exp_process(meta_info, guid)

        # We have the interfaces up, horray
        if (check_if(ifname) and
                check_meta(meta_info, IF_META_GRACE)):
            # We are all good
            if exp_process.is_alive() is False:
                exp_process.start()
        elif exp_process.is_alive():  # Interfaces down and we are running
            exp_process.terminate()
            exp_process = create_exp_process(meta_info, guid)

        time.sleep(IFUP_INTERVAL_CHECK)
