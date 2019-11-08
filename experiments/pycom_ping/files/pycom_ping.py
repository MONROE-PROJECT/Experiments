#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date: Nov 2019
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""
Simple wrapper to run ping on a pycom device using nb-iot.

The script will run forever on the specified interface.
All default values are configurable from the scheduler.
The output will be formated into a json object suitable for storage in the
MONROE db.
"""
import pyboard
import json
import re
import time

# Configuration
CONFIGFILE = '/monroe/config'

# Default values (overwritable from the scheduler)
EXPCONFIG = {
        "guid": "no.guid.in.config.file",  # Should be overridden by scheduler
        "nodeid": "fake.nodeid",
        "server": "8.8.8.8",  # ping target
        "interval": 5000,  # time in milliseconds between successive packets
        "dataversion": 1,
	    "size":56,
        "device": "/dev/pycom/board0",
#        "device": "/dev/tty.usbserial-DQ00DARH",
        "apn": "lpwa.telia.iot",
        "type": "LTE.IP",  #LTE.IP or LTE.IPV4V6 defualt LTE.IP
        "band": None,   # scans all bands
        "dataid": "MONROE.EXP.NBPING",
        "export_interval": 5.0,
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "dns_servers": ['8.8.8.8', '4.4.4.4'],
        "DEBUG": False
        }

def pyexec(cmd=None, pyb=None):
    """Returns a translated str"""
    if cmd and pyb:
        return pyb.exec(cmd).decode('utf-8').replace('/r/n', '/n')
    else:
        return ""

if __name__ == '__main__':
    """The main thread."""

    # Try to get the experiment config as provided by the scheduler
    try:
        with open(CONFIGFILE) as configfd:
            EXPCONFIG.update(json.load(configfd))
    except Exception as e:
        print ("Cannot retrive expconfig {}".format(e))
        EXPCONFIG['DEBUG'] = True

    if not EXPCONFIG['DEBUG']:
        import monroe_exporter
    else:
        EXPCONFIG['verbosity'] = 3


    # Short hand variables and check so we have all variables we need
    try:
        guid=EXPCONFIG['guid']
        nodeid=EXPCONFIG['nodeid']
        verbosity = EXPCONFIG['verbosity']
        dataid = EXPCONFIG['dataid']
        dataversion = EXPCONFIG['dataversion']
        band=EXPCONFIG['band']
        resultdir=EXPCONFIG['resultdir']
        export_interval=EXPCONFIG['export_interval']
        device_path=EXPCONFIG['device']
        apn=EXPCONFIG['apn']
        interval = float(EXPCONFIG['interval']/1000.0)
        server = EXPCONFIG['server']
        pktsize = EXPCONFIG['size']
        dns_servers = EXPCONFIG['dns_servers']
        iptype = EXPCONFIG['type']
    except Exception as e:
        print ("Missing expconfig variable {}".format(e))
        raise e

    if verbosity > 2:
        print (EXPCONFIG)

    if not EXPCONFIG['DEBUG']:
        monroe_exporter.initalize(export_interval, resultdir)

    #Load the helper functions
    if verbosity > 1:
        print(f"Loading the board: {device_path}")
    pyb = pyboard.Pyboard(device=device_path)
    if verbosity > 1:
        print(f"Initalizing the board: {device_path}")
    pyb.enter_raw_repl()
    if pyb.execfile(filename="fipy-helper-functions.py") != b'':
        print("Failed to load pycom helper functions")
        raise Exception("Failed to load pycom helper functions")

    if verbosity > 1:
        print(f"Getting ICCID: ", end = '', flush=True)
    iccid = pyexec('get_iccid()', pyb)
    if verbosity > 1:
        print(f"{iccid}")

    assert(iccid)

    #Setup connections
    if verbosity > 1:
        print(f"Setting up dns {dns_servers}: ", end = '', flush=True)
    res = pyexec(f'set_dns({dns_servers})', pyb)
    if verbosity > 1:
        print(f"{res}")

    if verbosity > 1:
        print(f'Setting up nbiot (apn="{apn}",band={band}, type={iptype}): ', end = '', flush=True)
    res = pyexec(f'set_nbiot(apn="{apn}",band={band}, type={iptype})', pyb)
    if verbosity > 1:
        print(f"{res}")

    # TODO: Check if lte is setup ok ....
    cmd = f'ping(host="{server}", count=1, size={pktsize})'

    seq = 0
    while "Connected" == pyexec('get_connection_status()', pyb):
        if verbosity > 2:
            print(f'Executing {cmd}: ', end = '', flush=True)
        try:
            res = ""
            res = pyexec(cmd, pyb)
            exp_result = json.loads(res)
        except Exception as e:
            if verbosity > 2:
                print('---> ', end = '', flush=True)
            print(f"Failed execution/parsing of {cmd} (got {res})")
            raise e

        if exp_result and exp_result.get("n_recv",0) > 0:
            msg = {
                    'Bytes': int(exp_result['bytes']),
                    'Host': server,
                    'Rtt': float(exp_result["rtts"][0]),   # We only have one value since count = 1
                    'SequenceNumber': int(seq),
                    'Timestamp': time.time(),
                    "Guid": guid,
                    "DataId": dataid,
                    "DataVersion": dataversion,
                    "NodeId": nodeid,
                    "Iccid": iccid,
                    "Operator": apn
                    }
        else:  # We lost the interface or did not get a reply
            msg = {
                    'Host': server,
                    'SequenceNumber': int(seq),
                    'Timestamp': time.time(),
                    "Guid": guid,
                    "DataId": dataid,
                    "DataVersion": dataversion,
                    "NodeId": nodeid,
                    "Iccid": iccid,
                    "Operator": apn
                    }

        if verbosity > 2:
            print (msg)
        if not EXPCONFIG['DEBUG']:
            # We have already initalized the exporter with the export dir
            monroe_exporter.save_output(msg)
        seq += 1
        time.sleep(interval)
    # Cleanup
    if verbosity > 1:
        print ("We are not connected(anymore), cleaning up pycom board")
    pyb.exit_raw_repl()
