#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date: May 2016
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""
Simple wrapper to run fping on a given host.

The script will run forever on the specified interface.
All default values are configurable from the scheduler.
The output will be formated into a json object suitable for storage in the
MONROE db.
"""
import zmq
import json
import sys
from multiprocessing import Process, Manager
import subprocess
import netifaces
import re
import time
import signal
import monroe_exporter

# Configuration
# Configuration
DEBUG = False
CONFIGFILE = '/monroe/config'

# Default values (overwritable from the scheduler)
# Can only be updated from the main thread and ONLY before any
# other processes are started
EXPCONFIG = {
        "guid": "no.guid.in.config.file",  # Should be overridden by scheduler
        "zmqport": "tcp://172.17.0.1:5556",
        "nodeid": "fake.nodeid",
        "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
        "server": "8.8.8.8",  # ping target
        "interval": 1000,  # time in milliseconds between successive packets
        "dataversion": 2,
        "dataid": "MONROE.EXP.PING",
        "meta_grace": 120,  # Grace period to wait for interface metadata
        "ifup_interval_check": 5,  # Interval to check if interface is up
        "export_interval": 5.0,
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "modeminterfacename": "InternalInterface",
        "interfacename": "eth0",  # Interface to run the experiment on
        "interfaces_without_metadata": ["eth0",
                                        "wlan0"]  # Manual metadata on these IF
        }


def run_exp(meta_info, expconfig):

    global FPING_PROCESS
    # Set some variables for saving data every export_interval
    monroe_exporter.initalize(expconfig['export_interval'],
                              expconfig['resultdir'])

    ifname = meta_info[expconfig["modeminterfacename"]]
    interval = float(expconfig['interval']/1000.0)
    server = expconfig['server']
    cmd = ["fping",
           "-I", ifname,
           "-D",
           "-c", "1",
           server]
    # Regexp to parse fping ouput from command
    r = re.compile(r'^\[(?P<ts>[0-9]+\.[0-9]+)\] (?P<host>[^ ]+) : \[(?P<seq>[0-9]+)\], (?P<bytes>\d+) bytes, (?P<rtt>[0-9]+(?:\.[0-9]+)?) ms \(.*\)$')

    # This is the inner loop where we wait for output from fping
    # This will run until we get a interface hickup, where the process will be
    # killed from parent process.
    seq = 0
    while True:
        popen = subprocess.Popen(cmd,
                                 stdout=subprocess.PIPE,
                                 bufsize=1)
        output = popen.stdout.readline()
        m = r.match(output)
        if m is not None:  # We could send and got a reply
            # keys are defined in regexp compilation. Nice!
            exp_result = m.groupdict()

            msg = {
                            'Bytes': int(exp_result['bytes']),
                            'Host': exp_result['host'],
                            'Rtt': float(exp_result['rtt']),
                            'SequenceNumber': int(seq),
                            'Timestamp': float(exp_result['ts']),
                            "Guid": expconfig['guid'],
                            "DataId": expconfig['dataid'],
                            "DataVersion": expconfig['dataversion'],
                            "NodeId": expconfig['nodeid'],
                            "Iccid": meta_info["ICCID"],
                            "Operator": meta_info["Operator"]
                  }
        else:  # We lost the interface or did not get a reply
            msg = {
                            'Host': server,
                            'SequenceNumber': int(seq),
                            'Timestamp': time.time(),
                            "Guid": expconfig['guid'],
                            "DataId": expconfig['dataid'],
                            "DataVersion": expconfig['dataversion'],
                            "NodeId": expconfig['nodeid'],
                            "Iccid": meta_info["ICCID"],
                            "Operator": meta_info["Operator"]
                   }

        if expconfig['verbosity'] > 2:
            print msg
        if not DEBUG:
            # We have already initalized the exporter with the export dir
            monroe_exporter.save_output(msg)
        seq += 1
        time.sleep(interval)
    # Cleanup
    if expconfig['verbosity'] > 1:
        print "Cleaning up fping process"
    popen.stdout.close()
    popen.terminate()
    popen.kill()


def metadata(meta_ifinfo, ifname, expconfig):
    """Seperate process that attach to the ZeroMQ socket as a subscriber.

        Will listen forever to messages with topic defined in topic and update
        the meta_ifinfo dictionary (a Manager dict).
    """
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(expconfig['zmqport'])
    socket.setsockopt(zmq.SUBSCRIBE, expconfig['modem_metadata_topic'])
    # End Attach
    while True:
        data = socket.recv()
        try:
            ifinfo = json.loads(data.split(" ", 1)[1])
            if (expconfig["modeminterfacename"] in ifinfo and
                    ifinfo[expconfig["modeminterfacename"]] == ifname):
                # In place manipulation of the reference variable
                for key, value in ifinfo.iteritems():
                    meta_ifinfo[key] = value
        except Exception as e:
            if expconfig['verbosity'] > 0:
                print ("Cannot get modem metadata in http container"
                       "error : {} , {}").format(e, expconfig['guid'])
            pass


# Helper functions could be moved to monroe_utils
def check_if(ifname):
    """Check if interface is up and have got an IP address."""
    return (ifname in netifaces.interfaces() and
            netifaces.AF_INET in netifaces.ifaddresses(ifname))


def check_meta(info, graceperiod, expconfig):
    """Check if we have recieved required information within graceperiod."""
    return (expconfig["modeminterfacename"] in info and
            "Operator" in info and
            "Timestamp" in info and
            time.time() - info["Timestamp"] < graceperiod)


def add_manual_metadata_information(info, ifname, expconfig):
    """Only used for local interfaces that do not have any metadata information.

       Normally eth0 and wlan0.
    """
    info[expconfig["modeminterfacename"]] = ifname
    info["ICCID"] = ifname
    info["Operator"] = ifname
    info["Timestamp"] = time.time()


def create_meta_process(ifname, expconfig):
    """Create a meta process and a shared dict for modem metadata state."""
    meta_info = Manager().dict()
    process = Process(target=metadata,
                      args=(meta_info, ifname, expconfig, ))
    process.daemon = True
    return (meta_info, process)


def create_exp_process(meta_info, expconfig):
    """This create a experiment thread."""
    process = Process(target=run_exp, args=(meta_info, expconfig, ))
    process.daemon = True
    return process


if __name__ == '__main__':
    """The main thread control the processes (experiment/metadata)."""

    if not DEBUG:
        import monroe_exporter
        # Try to get the experiment config as provided by the scheduler
        try:
            with open(CONFIGFILE) as configfd:
                EXPCONFIG.update(json.load(configfd))
        except Exception as e:
            print "Cannot retrive expconfig {}".format(e)
            raise e
    else:
        # We are in debug state always put out all information
        EXPCONFIG['verbosity'] = 3

    # Short hand variables and check so we have all variables we need
    try:
        ifname = EXPCONFIG['interfacename']
        if_without_metadata = EXPCONFIG['interfaces_without_metadata']
        meta_grace = EXPCONFIG['meta_grace']
        ifup_interval_check = EXPCONFIG['ifup_interval_check']
        EXPCONFIG['guid']
        EXPCONFIG['modem_metadata_topic']
        EXPCONFIG['zmqport']
        EXPCONFIG['nodeid']
        EXPCONFIG['verbosity']
        EXPCONFIG['resultdir']
        EXPCONFIG['export_interval']
        EXPCONFIG['modeminterfacename']
    except Exception as e:
        print "Missing expconfig variable {}".format(e)
        raise e

    if EXPCONFIG['verbosity'] > 2:
        print EXPCONFIG
    # Create a process for getting the metadata
    # (could have used a thread as well but this is true multiprocessing)
    meta_info, meta_process = create_meta_process(ifname, EXPCONFIG)
    meta_process.start()

    # Create a experiment script
    exp_process = exp_process = create_exp_process(meta_info, EXPCONFIG)

    # Control the processes
    while True:
        # If meta dies recreate and start it (should not happen)
        if not meta_process.is_alive():
            # This is serious as we will not receive uptodate information
            if exp_process.is_alive():  # Clean up the exp_thread
                exp_process.terminate()

            # The dict may have been corrupt so recreate that one
            meta_info, meta_process = create_meta_process(ifname, EXPCONFIG)
            meta_process.start()

            exp_process = create_exp_process(meta_info, EXPCONFIG)

        # On these Interfaces we do net get modem information so we hack
        # in the required values by hand whcih will immeditaly terminate
        # metadata loop below
        if (check_if(ifname) and ifname in if_without_metadata):
            add_manual_metadata_information(meta_info, ifname, EXPCONFIG)

        # Do we have the interfaces up ?
        if (check_if(ifname) and check_meta(meta_info, meta_grace, EXPCONFIG)):
            # We are all good
            if EXPCONFIG['verbosity'] > 2:
                print "Interface {} is up".format(ifname)
            if exp_process.is_alive() is False:
                exp_process.start()
        elif exp_process.is_alive():
            if EXPCONFIG['verbosity'] > 2:
                print ("Interface {} is down and "
                       "experiment are running").format(ifname)
            # Interfaces down and we are running
            exp_process.terminate()
            exp_process = create_exp_process(meta_info, EXPCONFIG)

        time.sleep(ifup_interval_check)
