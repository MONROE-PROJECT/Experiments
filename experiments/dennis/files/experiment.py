#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Stefan Alfredsson
# Date: Dec 2017
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""
Experiment for quering DNS servers using all available interfaces

"""
import json
import zmq
import sys
import netifaces
import time
from subprocess import check_output
from multiprocessing import Process, Manager

import dnslib

# Configuration
DEBUG = False
CONFIGFILE = '/monroe/config'

# Default values (overwritable from the scheduler)
# Can only be updated from the main thread and ONLY before any
# other processes are started
EXPCONFIG = {
        "zmqport": "tcp://172.17.0.1:5556",
        "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
        "dataid": "MONROE.EXP.DENNIS",  #  Name of experiement
        "meta_grace": 120,  # Grace period to wait for interface metadata
        "exp_grace": 120,  # Grace period before killing experiment
        "meta_interval_check": 5,  # Interval to check if interface is up
        "verbosity": 1,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "addresses": "cdn.netflix.com,www.google.com",
        "time": 3600  # The maximum time in seconds for a download
        }

def run_exp(expconfig):
    """Seperate process that runs the experiment and collect the ouput.

        Will abort if the interface goes down.
    """

    # Get the interfaces from the metadata stream
    interfaces=get_interfaces(expconfig)

    if len(interfaces) < 1:
        print "No interfaces found. Nothing to do."
        return 

    
    for (ifname, op, ip) in interfaces:

        print ("---------- Testing interface {} {} {} ----------".format(ifname, op, ip)) 

        dnslib.set_dns(ifname)
        dnslib.set_defaultroute(ifname)

        try:
            print ("My external IP is {}".format(check_output("/usr/bin/curl ifconfig.co"))) # FIXME: use own servers instead of ifconfig.co
        except:
            pass


        for address in expconfig['addresses'].split(','):
            cmd = ["host", "{}".format(address)]
    
            output = ""
            try:
                output = check_output(cmd)
    
            except Exception as e:
                print "Execution or parsing failed: {}".format(e)
            
            print output
    
def get_interfaces(expconfig):
    """Listen to the metadata messages to find the available operators

    """
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(expconfig['zmqport'])
    socket.setsockopt(zmq.SUBSCRIBE, bytes(expconfig['modem_metadata_topic']))
    #socket.settimeout(5.0)

    interfaces=[]

    start=time.time()

    # Run for at least 30 seconds to collect all metadata.
    while len(interfaces) < 2 and time.time() - start < 30:
        data = socket.recv()
        try:
            topic = data.split(" ", 1)[0]
            msg = json.loads(data.split(" ", 1)[1])
            if topic.startswith(expconfig['modem_metadata_topic']):
                    interface=msg['InternalInterface']
                    op=msg['Operator']
                    ip=msg['IPAddress']

                    if not (interface, op, ip) in interfaces:
                        if expconfig['verbosity'] > 1:
                            print("Adding interface {}".format(interface))
                        interfaces.append((interface, op, ip))

            if expconfig['verbosity'] > 2:
                print "zmq message", topic, msg
        except Exception as e:
            if expconfig['verbosity'] > 0:
                print ("Cannot retrive expconfig {}".format(e))
            pass

    return interfaces


# Helper functions
def check_if(ifname):
    """Checks if "internal" interface is up and have got an IP address.

       This check is to ensure that we have an interface in the experiment
       container and that we have a internal IP address.
    """
    return (ifname in netifaces.interfaces() and
            netifaces.AF_INET in netifaces.ifaddresses(ifname))


def create_and_run_exp_process(expconfig):
    """Creates the experiment process."""
    process = Process(target=run_exp, args=(expconfig, ))
    process.daemon = True
    process.start()
    return process


if __name__ == '__main__':
    """The main thread control the processes (experiment/metadata))."""

    start_time = time.time()

    if not DEBUG:
        # Try to get the experiment config as provided by the scheduler
        try:
            with open(CONFIGFILE) as configfd:
                EXPCONFIG.update(json.load(configfd))
        except Exception as e:
            print "Cannot retrive expconfig {}".format(e)
            sys.exit(1)
    else:
        # We are in debug state always put out all information
        EXPCONFIG['verbosity'] = 3

    # Short hand variables and check so we have all variables we need
    try:
        EXPCONFIG['guid']
        EXPCONFIG['modem_metadata_topic']
        EXPCONFIG['zmqport']
        EXPCONFIG['verbosity']
        EXPCONFIG['resultdir']
        EXPCONFIG['addresses']
    except Exception as e:
        print "Missing expconfig variable {}".format(e)
        sys.exit(1)

    if EXPCONFIG['verbosity'] > 1:
        print "Starting experiment"

    exp_process = create_and_run_exp_process(EXPCONFIG)

    exp_grace=EXPCONFIG['exp_grace']

    while exp_process.is_alive():
        time.sleep(1)

    elapsed = time.time() - start_time

    if EXPCONFIG['verbosity'] > 1:
        print "Finished after {}".format(elapsed)

