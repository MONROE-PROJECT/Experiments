#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: M. Rajiullah
# Date: June 2020
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE (+ 5Genesis) project

"""
Simple wrapper to run a coap client on a given host.

The script will run on the specified interface.
All default values are configurable from the scheduler.
The output will be formated into a json object suitable for storage in the
MONROE db.
"""
import zmq
import json
import sys

import subprocess
import netifaces
import re
import time
import signal
import monroe_exporter
from subprocess import check_output, CalledProcessError
from multiprocessing import Process, Manager

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
        "server": "130.243.27.221",  # ping target
        "interval": 1000,  # time in milliseconds between successive packets
        "dataversion": 2,
	    "msgLen":100,
        "msgInterval":2,
        "numMsgs":4,
        "time": 100, #max time for exps
        "dataid": "MONROE.EXP.COAP",
        "meta_grace": 120,  # Grace period to wait for interface metadata
        "exp_grace": 120,  # Grace period before killing experiment
        "ifup_interval_check": 5,  # Interval to check if interface is up
        "export_interval": 5.0,
        "verbosity": 3,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "modeminterfacename": "InternalInterface",
        "interfacename": "op0",  # Interface to run the experiment on
        "allowed_interfaces": ["op0"],
        "interfaces_without_metadata": ["eth0"]  # Manual metadata on these IF
        }


def run_exp(meta_info, expconfig):


    # Set some variables for saving data every export_interval
    monroe_exporter.initalize(expconfig['export_interval'],
                              expconfig['resultdir'])

    ifname = meta_info[expconfig["modeminterfacename"]]
    interval = float(expconfig['interval']/1000.0)
    server = expconfig['server']

    seq = expconfig['numMsgs']
    msgLen=expconfig['msgLen']
    msgInterval=expconfig['msgInterval']
    cmd = ["python3", "monroe-coap-client.py",server, str(msgLen), str(seq), str(msgInterval)]
    rtt=[]
    owd=[]

    output=None

    #print (cmd)
    try:
        output=check_output(cmd)
#	output = output.strip(' \t\r\n\0')

    except CalledProcessError as error:
        if error.returncode == 28:
	    print "Time limit exceeded"

    msg = json.loads(output)

    msg.update({
            "Guid": expconfig['guid'],
            "DataId": expconfig['dataid'],
            "DataVersion": expconfig['dataversion'],
            "NodeId": expconfig['nodeid'],
            "Timestamp": time.time(),
            "Iccid": meta_info["ICCID"],
            "Operator": meta_info["Operator"],
            "IPAddress": meta_info["IPAddress"],
            #"InternalIPAddress": meta_info["InternalIPAddress"],
            "LAC":meta_info["LAC"],
            "RSSI":meta_info["RSSI"],
            "RSRP":meta_info["RSRP"],
            "RSRQ":meta_info["RSRQ"],
            "deviceMode":meta_info["DeviceMode"],
            "deviceSubMode":meta_info["DeviceSubmode"],
            "numMsgs":seq,
            "msgInterval":msgInterval
             })

    with open('/monroe/results/'+str(msg["NodeId"])+'_'+str(msg["DataId"])+'_'+str(msg["Timestamp"])+'.json', 'w') as outfile:
    	json.dump(msg, outfile)
    if expconfig['verbosity'] > 2:
            print msg
    #if not DEBUG:
     #       monroe_exporter.save_output(msg, expconfig['resultdir'])


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
            topic,msg=data.split(" ",1)
            #ifinfo = json.loads(data.split(" ", 1)[1])
            ifinfo = json.loads(msg)
            if (expconfig["modeminterfacename"] in ifinfo and "UPDATE" in topic and
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
        exp_grace = EXPCONFIG['exp_grace'] + EXPCONFIG['time']
        ifup_interval_check = EXPCONFIG['ifup_interval_check']
        EXPCONFIG['guid']
        EXPCONFIG['modem_metadata_topic']
        EXPCONFIG['zmqport']
        EXPCONFIG['nodeid']
        EXPCONFIG['verbosity']
        EXPCONFIG['resultdir']
        EXPCONFIG['export_interval']
        EXPCONFIG['modeminterfacename']
        EXPCONFIG['server']
        EXPCONFIG['msgLen']
        EXPCONFIG['msgInterval']
        EXPCONFIG['numMsgs']
        EXPCONFIG['msgInterval']

    except Exception as e:
        print "Missing expconfig variable {}".format(e)
        raise e

    if EXPCONFIG['verbosity'] > 2:
        print EXPCONFIG
    # Create a process for getting the metadata
    # (could have used a thread as well but this is true multiprocessing)
    meta_info, meta_process = create_meta_process(ifname, EXPCONFIG)
    meta_process.start()

    if EXPCONFIG['verbosity'] > 1:
    	print "Starting Experiment Run on if : {}".format(ifname)

    # On these Interfaces we do net get modem information so we hack
    # in the required values by hand whcih will immeditaly terminate
    # metadata loop below
    if (check_if(ifname) and ifname in if_without_metadata):
    	add_manual_metadata_information(meta_info, ifname, EXPCONFIG)
#
    # Try to get metadadata
    # if the metadata process dies we retry until the IF_META_GRACE is up
    start_time = time.time()
    while (time.time() - start_time < meta_grace and
    	not check_meta(meta_info, meta_grace, EXPCONFIG)):
        if not meta_process.is_alive():
        	# This is serious as we will not receive updates
                # The meta_info dict may have been corrupt so recreate that one
        	meta_info, meta_process = create_meta_process(ifname,
                                                              EXPCONFIG)
                meta_process.start()
        if EXPCONFIG['verbosity'] > 1:
        	print "Trying to get metadata"
        time.sleep(ifup_interval_check)

    # Ok we did not get any information within the grace period
    # we give up on that interface
    if not check_meta(meta_info, meta_grace, EXPCONFIG):
    	if EXPCONFIG['verbosity'] > 1:
    		print "No Metadata continuing"

    # Ok we have some information lets start the experiment script



    if EXPCONFIG['verbosity'] > 1:
    	print "Starting experiment"

    # Create a experiment process
    start_time_exp = time.time()
    exp_process = create_exp_process(meta_info, EXPCONFIG)
    exp_process.start()

    while (time.time() - start_time_exp < exp_grace and
                     exp_process.is_alive()):
    	if not (check_if(ifname) and check_meta(meta_info,meta_grace,EXPCONFIG)):
		if EXPCONFIG['verbosity'] > 0:
                	print "Interface went down during a experiment"
                break
        elapsed_exp = time.time() - start_time_exp
        if EXPCONFIG['verbosity'] > 1:
        	print "Running Experiment for {} s".format(elapsed_exp)
        time.sleep(ifup_interval_check)

    if exp_process.is_alive():
    	exp_process.terminate()
    if meta_process.is_alive():
    	meta_process.terminate()

    elapsed = time.time() - start_time
    if EXPCONFIG['verbosity'] > 1:
    	print "Finished {} after {}".format(ifname, elapsed)
    #time.sleep(time_between_experiments)

    #if EXPCONFIG['verbosity'] > 1:
    #    print ("Interfaces {} "
    #           "done, exiting").format(allowed_interfaces)
