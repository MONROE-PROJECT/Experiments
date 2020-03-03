#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date:February 2019
# License: GNU General Public License v3

"""
Simple wrapper to run iperf/iperf3 on a given host.

The script will run on all specified interfaces.
All default values are configurable from the scheduler.
The output will be formated into a json object (not suitable for db import).
"""

import zmq
import json
from datetime import datetime
import time
import subprocess
import netifaces
from flatten_json import flatten

# Configuration
DEBUG = False
CONFIGFILE = '/monroe/config'

# Default values (overwritable from the scheduler)
# Can only be updated from the main thread and ONLY before any
# other processes are started
EXPCONFIG = {
        "zmqport": "tcp://172.17.0.1:5556",
        "guid": "fake.guid",  # Need to be overriden
        "nodeid": "virtual",
        "metadata_topic": "MONROE.META",
        "dataid": "5GENESIS.EXP.IPERF",
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "flatten_delimiter": '.',
        "server": "130.243.27.222",
        "protocol": "tcp",
        "duration": 10,
        "bandwidth": 0,   # Default for TCP for UDP is 1M default
        "interfaces": "eth0" ,  # delimited by ',', eg "eth0,eth1"
        "iperfversion": 3
        }

def get_recursively(search_dict, field):
    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key which consists
    of the field provided.
    Adapted from : https://stackoverflow.com/a/20254842
    """
    fields_found = []

    for key, value in search_dict.iteritems():
        if field in key:
            fields_found.append(key)
        elif isinstance(value, dict):
            results = get_recursively(value, field)
            for result in results:
                fields_found.append(result)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    more_results = get_recursively(item, field)
                    for another_result in more_results:
                        fields_found.append(another_result)
    return fields_found

def check_if(ifname):
    """Check if interface is up and have got an IP address."""
    return (ifname in netifaces.interfaces() and
            netifaces.AF_INET in netifaces.ifaddresses(ifname))

def run_iperf3(server, sourceip, protocol, duration, bandwidth):
    """Runs iperf3 and returns the resluts as a dictionary."""
    cmd = [ "iperf3",
            "--json",
            "--bind", sourceip,
            "--time", duration,
            "--bandwidth", bandwidth,
            "--client", server
            ]
    if protocol == "udp":
        cmd.append("--udp")

    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    msg = json.load(popen.stdout)
    return msg

def run_iperf(server, sourceip, protocol, duration, bandwidth):
    """
    Runs iperf and returns the resluts (or error message) as a dictionary.
    Headers are from https://bit.ly/2EmbVSV and https://bit.ly/2VpGNc8
    timestamp,
    source_address,
    source_port,
    destination_address,
    destination_port,
    transferID,
    interval,
    transferred_bytes,
    bits_per_second
    """
    cmd = [ "iperf",
            "--enhancedreports",
            "--reportstyle", "C",
            "--time", duration,
            "--bandwidth", bandwidth,
            "--bind", sourceip,
            "--client", server
            ]
    if protocol == "udp":
        cmd.append("--udp")
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE, bufsize=1)
    output = popen.stdout.readline().rstrip()
    if output and  len(output.split(',')) > 8:
        csv = output.split(',')
        msg = {
            "timestamp" : float(csv[0]),
            "source_address": str(csv[1]),
            "source_port": int(csv[2]),
            "destination_address": str(csv[3]),
            "destination_port": int(csv[4]),
            "transferID": int(csv[5]),
            "interval": str(csv[6]),
            "transferred_bytes": int(csv[7]),
            "bits_per_second": int(csv[8])
        }
    else:
        msg = {
            "error": popen.stderr.readline().rstrip()
        }
    return msg



if __name__ == '__main__':
    """The main thread control the processes. """

    if not DEBUG:
        # Try to get the experiment config as provided by the scheduler
        try:
            with open(CONFIGFILE) as configfd:
		fileconfig = json.load(configfd)
		#Set the default values for iperf
		if 'bandwidth' not in fileconfig and fileconfig.get('protocol') == 'udp':
		  fileconfig['bandwidth'] = '1M'

                EXPCONFIG.update(fileconfig)
        except Exception as e:
            print ("Cannot retrive expconfig {}".format(e))
            raise e
    else:
        # We are in debug state always put out all information
        EXPCONFIG['verbosity'] = 3

    # Short hand variables and assertion/check so we have all variables we need
    try:
        interfaces = list(str(EXPCONFIG['interfaces']).split(','))
        guid = str(EXPCONFIG['guid'])
        dataid = str(EXPCONFIG['dataid'])
        nodeid = str(EXPCONFIG['nodeid'])
        zmqport = str(EXPCONFIG['zmqport'])
        topic = str(EXPCONFIG['metadata_topic'])
        verbosity = int(EXPCONFIG['verbosity'])
        resultdir = str(EXPCONFIG['resultdir'])
        server = str(EXPCONFIG['server'])
        version = int(EXPCONFIG['iperfversion'])
        protocol = str(EXPCONFIG['protocol'])
        duration = str(int(EXPCONFIG['duration']))
        bandwidth = str(EXPCONFIG['bandwidth'])
        flatten_delimiter = str(EXPCONFIG['flatten_delimiter'])
    except Exception as e:
        print ("Missing or wrong format on expconfig variable {}".format(e))
        raise e

    if verbosity > 2:
        print EXPCONFIG
        print interfaces

    # Attach to the ZeroMQ socket as a subscriber and start listen to
    # metadata, this does notning for now
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(zmqport)
    socket.setsockopt(zmq.SUBSCRIBE, topic)
    # End Attach

    if verbosity > 1:
        print ("[{}] Starting experiment".format(datetime.now()))

    for ifname in interfaces:
        if check_if(ifname):
            # We are all good
            ips = [x.get('addr',None) for x in netifaces.ifaddresses(ifname)[netifaces.AF_INET]]
            if verbosity > 2:
                print ("Interface {} is up with ip(s) : {}".format(ifname, ips))

            for ip in ips:
                if verbosity > 2:
                        print (("Executing iperf{version}(3/2) from {ifname}({ip}) "
                                "to {server} using {protocol} with {bandwidth} for "
                                "{duration} seconds").format(version=version,
                                                            ifname=ifname,
                                                            ip=ip,
                                                            server=server,
                                                            protocol=protocol,
                                                            duration=duration,
                                                            bandwidth=bandwidth))

                try:
                    if version == 3:
                        exp_res = run_iperf3(server=server,
                                             sourceip=ip,
                                             protocol=protocol,
                                             duration=duration,
                                             bandwidth=bandwidth)
                    else:
                        exp_res = run_iperf(server=server,
                                            sourceip=ip,
                                            protocol=protocol,
                                            duration=duration,
                                            bandwidth=bandwidth)
                except Exception as e:
                    print "Could not execute iperf{}, error: {}".format(version,e)
                    raise e
                msg = {
                    "Timestamp": time.time(),
                    "Guid": guid,
                    "DataId": dataid,
                    "DataVersion": version,
                    "NodeId": nodeid,
                    "Interface": ifname,
                    "Protocol": protocol,
                    "Results": exp_res
                }
                if protocol == "udp" and version != 3:
                    msg["Note"] = "Warning: UDP results is only stable with iperf3"
                    print ("Warning: UDP results is only stable with iperf3")

                path = ("{resultdir}/{dataid}.{version}.{protocol}"
                        "_{nodeid}_{ts}_{ifname}_{ip}.json").format(resultdir=resultdir,
                                                                    dataid=dataid,
                                                                    version=version,
                                                                    nodeid=nodeid,
                                                                    protocol=protocol,
                                                                    ts=msg['Timestamp'],
                                                                    ifname=ifname,
                                                                    ip=ip)

                # Flatten the output
                problematic_keys = get_recursively(msg, flatten_delimiter)
                if problematic_keys and verbosity > 1:
                    print ("Warning: these keys might be compromised by flattening:"
                           " {}".format(problematic_keys))
                msg = flatten(msg, flatten_delimiter)
                if verbosity > 2:
                    print ("Saving experiment results to {}".format(path))
                    print (json.dumps(msg,indent=4, sort_keys=True))

                # Save the file
                with open(path, 'w') as outfile:
                    json.dump(msg, outfile)
    if verbosity > 1:
        print ("[{}] Finished the experiment".format(datetime.now()))
