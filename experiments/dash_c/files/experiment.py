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
        "dataid": "5GENESIS.EXP.DASHC",
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "flatten_delimiter": '.',
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

def run_exp(url, duration):
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
    cmd = [ "dash.exe", "play",
            "-logname", "dashc.log",
            "-turnlogon", "true",
            "-subfolder", ".",
            url
            ]

    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE, bufsize=1)
    log = []
    #Strip the header
    output = popen.stdout.readline().rstrip()
    while not output:
        output = popen.stdout.readline().rstrip()
        if output and len(output.split()) > 8:
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
                "error": popen.stderr.readline().rstrip()
            }
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
            print ("Cannot retrive expconfig {}".format(e))
            raise e
    else:
        # We are in debug state always put out all information
        EXPCONFIG['verbosity'] = 3

    # Short hand variables and assertion/check so we have all variables we need
    try:
        guid = str(EXPCONFIG['guid'])
        dataid = str(EXPCONFIG['dataid'])
        nodeid = str(EXPCONFIG['nodeid'])
        zmqport = str(EXPCONFIG['zmqport'])
        topic = str(EXPCONFIG['metadata_topic'])
        verbosity = int(EXPCONFIG['verbosity'])
        resultdir = str(EXPCONFIG['resultdir'])
        url = str(EXPCONFIG['url'])
        duration = str(int(EXPCONFIG['duration']))
        flatten_delimiter = str(EXPCONFIG['flatten_delimiter'])
    except Exception as e:
        print ("Missing or wrong format on expconfig variable {}".format(e))
        raise e

    if verbosity > 2:
        print EXPCONFIG

    # Attach to the ZeroMQ socket as a subscriber and start listen to
    # metadata, this does notning for now
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(zmqport)
    socket.setsockopt(zmq.SUBSCRIBE, topic)
    # End Attach

    if verbosity > 1:
        print ("[{}] Starting experiment".format(datetime.now()))

    if verbosity > 2:
        print (("Executing dashc to {url} for"
                " {duration} seconds").format(url=url, duration=duration,))
    try:
        exp_res = run_exp(url=url,duration=duration)
    except Exception as e:
        print "Could not execute dashc{}, error: {}".format(version,e)
        raise e

    msg = {
            "Timestamp": time.time(),
            "Guid": guid,
            "DataId": dataid,
            "DataVersion": version,
            "NodeId": nodeid,
            "Results": exp_res
            }

    path = ("{resultdir}/"
            "{dataid}_{nodeid}_{ts}.json").format(resultdir=resultdir,
                                                  duration=duration,
                                                  nodeid=nodeid,
                                                  ts=msg['Timestamp'])

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
