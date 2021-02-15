#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date:April 2020
# License: GNU General Public License v3

"""
Simple wrapper to run dashc on a given host.

The script will use the default route (ie no interface can be specified).
All default values are configurable from the scheduler/elcm.
The output will be formated into a json object suitable for db import.
Example dash file from :
`
Jason J. Quinlan, Ahmed H. Zahran, Cormac J. Sreenan,
"Datasets for AVC (H.264) and HEVC (H.265) Evaluation of Dynamic Adaptive
Streaming over HTTP (DASH)". In Proceedings of the 7th ACM Multimedia Systems
Conference 2016, Klagenfurt am Wörthersee, Austria. May 10-13, 2016.
`
URL: http://143.239.75.241/~jq5/www_dataset_temp/
"""

import zmq
import json
from datetime import datetime
import time
from subprocess32 import TimeoutExpired, run, CalledProcessError, PIPE
import netifaces as ni
from flatten_json import flatten
import os
import re

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
        "dataid": "5GENESIS.EXP.DASHC",
        "dataversion": 1,
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "flatten_delimiter": '.',
        "allowed_interfaces": ["ens160", "ens192", "eth0"],  # Interfaces to run the experiment on
        #www.cs.ucc.ie
        "url": "http://143.239.75.241/~jq5/www_dataset_temp/x264_4sec/bbb_10min/DASH_Files/VOD/bbb_enc_10min_x264_dash.mpd",
        "duration": 900,
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
    return (ifname in ni.interfaces() and
        ni.AF_INET in ni.ifaddresses(ifname))

def set_default_gw(ifname):
    del_gw = ["route", "del", "default"]
    add_gw = ["route", "add", "default", "gw" ]
    gw_ip = [g[0] for g in ni.gateways().get(ni.AF_INET, []) if g[1] == ifname]

    # Check so we actually got a gw for that interface
    if not gw_ip:
        print ("No gw set for {}".format(ifname))
        print ("Gws : {}".format(ni.gateways()))
        return False

    add_gw.extend([gw_ip[0], ifname])
    try:
        # We do not check delete as it might be that no default gw is set
        # We do set a timeout for 10 seconds as a indicationm that
        # something went bad though
        if verbosity > 2:
            print (del_gw)
        run(del_gw, timeout=10)
        if verbosity > 2:
            print (add_gw)
        #We check so this went OK
        run(add_gw, timeout=10, check=True)
        gws = ni.gateways()['default'].get(ni.AF_INET)

        if not gws:
            print ("Default gw could no be set")
            return False

        if gws[1] == ifname:
            print ("Source interface is set to {}".format(ifname))
        else:
            print ("Source interface {} is different from {}".format(gws[1],
                                                                     ifname))
            return False
    except (CalledProcessError, TimeoutExpired) as e:
        print ("Error in set default gw : {}".format(e))
        return False

    return True
def used_dns():
    cmd=["dig", "www.google.com","+noquestion", "+nocomments", "+noanswer"]
    try:
        out=run(cmd, timeout=10, check=True, stdout=PIPE).stdout
        start=out.find('SERVER: ') + 8
        end=out[start:].find('(')
        return out[start:start+end]
    except:
        return ""

def check_dns(dns_list):
    cmd=["dig", "www.google.com","+noquestion", "+nocomments", "+noanswer"]
    data=dns_list.replace("\n"," ")
    try:
        out=run(cmd, timeout=10, check=True, stdout=PIPE).stdout
        for line in out.splitlines():
            for ip in re.findall(r'(?:\d{1,3}\.)+(?:\d{1,3})',data):
                if ip in line:
                    print line
                    return True
    except (CalledProcessError, TimeoutExpired) as e:
            print ("Error in dns check : {}".format(e))

    return False

def add_dns(interface):
    str = ""
    try:
        with open('/dns') as dnsfile:
            dnsdata = dnsfile.readlines()
            print dnsdata
            dnslist = [ x.strip() for x in dnsdata ]
            for item in dnslist:
                if interface in item:
                    str += item.split('@')[0].replace("server=",
                        "nameserver ")
                    str += "\n"
        with open("/etc/resolv.conf", "w") as f:
            f.write(str)
    except:
        print("Could not find DNS file")
    else:
        print (str)
    return str

def run_exp(url, duration, logfile):
    """
    Runs dashc and returns the resluts as a dictionary.
        Seg_#
        Arr_time
        Del_Time
        Stall_Dur
        Rep_Level
        Del_Rate
        Act_Rate
        Byte_Size
        Buff_Level
    """
    resultdir, logname = os.path.split(logfile)
    cmd = [ "dashc.exe", "play",
            "-logname", logname,
            "-turnlogon", "true",
            "-subfolder", resultdir,
            url
            ]

    try:
        run(cmd, timeout=duration)
    except TimeoutExpired as e:
        if verbosity > 2:
            print ("Terminated after {}".format(duration))
    else:
        if verbosity > 2:
            print ("All downloaded")

    if verbosity > 2:
        print ("Start parsing of logfile")

    log = []
    with open(logfile) as fp:
        #Skip the headers
        output = fp.readline()
        for output in fp:
            output = output.rstrip()
            if len(output.split()) > 8:
                csv = output.split()
                msg = {
                    "Seg_#" :   int(csv[0]),
                    "Arr_time": int(csv[1]),
                    "Del_Time": int(csv[2]),
                    "Stall_Dur": int(csv[3]),
                    "Rep_Level": int(csv[4]),
                    "Del_Rate": int(csv[5]),
                    "Act_Rate": int(csv[6]),
                    "Byte_Size": int(csv[7]),
                    "Buff_Leveltimestamp": float(csv[8])
                }
            else:
                msg = {
                    "error": output
                }
            if verbosity > 2:
                print ("{}".format(msg))
            log.append(msg)

    return log

if __name__ == '__main__':
    """The main thread control the processes. """

    if not DEBUG:
        # Try to get the experiment config as provided by the scheduler
        try:
            with open(CONFIGFILE) as configfd:
                fileconfig = json.load(configfd)
                EXPCONFIG.update(fileconfig)
        except Exception as e:
            print ("Error: Cannot retrive expconfig {}".format(e))
            print("Warning: Enabling DEBUG and running with default parameters")
            DEBUG = True
            EXPCONFIG['verbosity'] = 3
    else:
        # We are in debug state always put out all information
        EXPCONFIG['verbosity'] = 3

    # Short hand variables and assertion/check so we have all variables we need
    try:
        allowed_interfaces = list(EXPCONFIG['allowed_interfaces'])
        guid = str(EXPCONFIG['guid'])
        dataid = str(EXPCONFIG['dataid'])
        dataversion = int(EXPCONFIG['dataversion'])
        nodeid = str(EXPCONFIG['nodeid'])
        zmqport = str(EXPCONFIG['zmqport'])
        topic = str(EXPCONFIG['metadata_topic'])
        verbosity = int(EXPCONFIG['verbosity'])
        resultdir = str(EXPCONFIG['resultdir'])
        url = str(EXPCONFIG['url'])
        duration = float(EXPCONFIG['duration'])
        flatten_delimiter = str(EXPCONFIG['flatten_delimiter'])
    except Exception as e:
        print ("Missing or wrong format on expconfig variable {}".format(e))
        raise e

    if verbosity > 2:
        print (EXPCONFIG)

    # Attach to the ZeroMQ socket as a subscriber and start listen to
    # metadata, this does notning for now
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(zmqport)
    socket.setsockopt(zmq.SUBSCRIBE, topic)
    # End Attach

    start_exp = time.time()
    print ("[{}] Starting experiment".format(datetime.now()))

    for ifname in allowed_interfaces:
        # Interface is not up we just skip that one
        if not check_if(ifname):
            print "Interface is not up {}".format(ifname)
            continue

        # set the source route
        if not set_default_gw(ifname):
            print "Could not set Interface {} as default GW".format(ifname)
            continue

        print "Configuring operator specific dns..(if any)"
        dns_list=add_dns(ifname)

        if not dns_list:
            print ("No Operator dns is configured")
            print ("Using dns : {}".format(used_dns()))
        elif check_dns(dns_list):
            print ("Operator dns is set properly")
        else:
            print ("Operator dns could not be set")
            #continue here ?

        if verbosity > 2:
            print (("Executing dashc play {url} for (max) "
                    " {duration} seconds on {iface}").format(url=url,
                                                             duration=duration,
                                                             iface=ifname))
        exp_ts=time.time()
        log_file="{}/dashc_{}_{}.log".format(resultdir,ifname,exp_ts)
        try:
            exp_res = run_exp(url=url,duration=duration, logfile=log_file)
        except Exception as e:
            print ("Could not execute dashc, error: {}".format(e))
            raise e

        msg = {
                "Timestamp": exp_ts,
                "Guid": guid,
                "DataId": dataid,
                "DataVersion": dataversion,
                "NodeId": nodeid,
                "Interface": ifname,
                "Results": exp_res
                }

        path = ("{resultdir}/"
                "{dataid}_{nodeid}_{ifname}_{ts}.json").format(dataid=dataid,
                                                      resultdir=resultdir,
                                                      duration=duration,
                                                      nodeid=nodeid,
                                                      ts=msg['Timestamp'],
                                                      ifname=ifname)

        # Flatten the output
        problematic_keys = get_recursively(msg, flatten_delimiter)
        if problematic_keys:
            print ("Warning: these keys might be compromised by flattening:"
                   " {}".format(problematic_keys))

        msg = flatten(msg, flatten_delimiter)
        if verbosity > 2:
            print ("Saving experiment results to {}".format(path))
            print (json.dumps(msg,indent=4, sort_keys=True))

        # Save the file
        with open(path, 'w') as outfile:
            json.dump(msg, outfile)

    print ("[{}] Finished the experiment it took {}".format(datetime.now(),
                                                            (time.time()
                                                            -start_exp)))
