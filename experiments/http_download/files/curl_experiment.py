#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date: June 2016
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""
Simple curl wrapper to download a url/file using curl.

The script will execute one experiment for each of the allowed_interfaces.
All default values are configurable from the scheduler.
The output will be formated into a json object suitable for storage in the
MONROE db.
"""
import json
import zmq
import netifaces
import time
from subprocess import check_output
from multiprocessing import Process, Manager

# Configuration
DEBUG = False
CONFIGFILE = '/monroe/config'

# Default values (overwritable from the scheduler)
# Can only be updated from the main thread and ONLY before any
# other processes are started
EXPCONFIG = {
        "guid": "no.guid.in.config.file",  # Should be overridden by scheduler
        "url": "http://193.10.227.25/test/1000M.zip",
        "size": 3*1024 - 1,  # The maximum size in Kbytes to download
        "time": 3600,  # The maximum time in seconds for a download
        "zmqport": "tcp://172.17.0.1:5556",
        "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
        "dataversion": 1,
        "dataid": "MONROE.EXP.HTTP.DOWNLOAD",
        "nodeid": "fake.nodeid",
        "meta_grace": 120,  # Grace period to wait for interface metadata
        "exp_grace": 120,  # Grace period before killing experiment
        "ifup_interval_check": 5,  # Interval to check if interface is up
        "time_between_experiments": 30,
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "modeminterfacename": "InternalInterface",
        "allowed_interfaces": ["usb0",
                               "usb1",
                               "usb2",
                               "wlan0",
                               "wwan2"],  # Interfaces to run the experiment on
        "interfaces_without_metadata": ["eth0",
                                        "wlan0"]  # Manual metadata on these IF
        }

# What to save from curl
CURL_METRICS = ('{ '
                '"Host": "%{remote_ip}", '
                '"Port": "%{remote_port}", '
                '"Speed": %{speed_download}, '
                '"Bytes": %{size_download}, '
                '"TotalTime": %{time_total}, '
                '"SetupTime": %{time_starttransfer} '
                '}')


def run_exp(meta_info, expconfig):
    """Seperate process that runs the experiment and collect the ouput.

        Will abort if the interface goes down.
    """
    ifname = meta_info.get(expconfig["modeminterfacename"],
                           meta_info['InterfaceName'])
    cmd = ["curl",
           "--raw",
           "--silent",
           "--write-out", "{}".format(CURL_METRICS),
           "--interface", "{}".format(ifname),
           "--max-time", "{}".format(expconfig['time']),
           "--range", "0-{}".format(expconfig['size']),
           "{}".format(expconfig['url'])]
    try:
        output = check_output(cmd)
        # Clean away leading and trailing whitespace
        output = output.strip(' \t\r\n\0')
        # Convert to JSON
        msg = json.loads(output)

        msg.update({
            "Guid": expconfig['guid'],
            "DataId": expconfig['dataid'],
            "DataVersion": expconfig['dataversion'],
            "NodeId": expconfig['nodeid'],
            "Timestamp": time.time(),
            "Iccid": meta_info["ICCID"],
            "Operator": meta_info["Operator"],
            "DownloadTime": msg["TotalTime"] - msg["SetupTime"],
            "SequenceNumber": 1
        })
        if expconfig['verbosity'] > 2:
            print msg
        if not DEBUG:
            monroe_exporter.save_output(msg, expconfig['resultdir'])
    except Exception as e:
        if expconfig['verbosity'] > 0:
            print "Execution or parsing failed: {}".format(e)


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
            if expconfig["modeminterfacename"] not in ifinfo:
                print ("Fallback to use InterfaceName as {} "
                       "do not exist").format(expconfig["modeminterfacename"])

            ifinfo_name = ifinfo.get(expconfig["modeminterfacename"],
                                     ifinfo['InterfaceName'])
            if ifinfo_name == ifname:
                # In place manipulation of the refrence variable
                for key, value in ifinfo.iteritems():
                    meta_ifinfo[key] = value
        except Exception as e:
            if expconfig['verbosity'] > 0:
                print ("Cannot get modem metadata in http container {}"
                       ", {}").format(e, expconfig['guid'])
            pass


# Helper functions
def check_if(ifname):
    """Check if interface is up and have got an IP address."""
    return (ifname in netifaces.interfaces() and
            netifaces.AF_INET in netifaces.ifaddresses(ifname))


def check_meta(info, graceperiod, expconfig):
    """Check if we have recieved required information within graceperiod."""
    return ((expconfig["modeminterfacename"] in info or
             "InterfaceName" in info) and
            "Operator" in info and
            "Timestamp" in info and
            time.time() - info["Timestamp"] < graceperiod)


def add_manual_metadata_information(info, ifname, expconfig):
    """Only used for local interfaces that do not have any metadata information.

       Normally eth0 and wlan0.
    """
    info["InterfaceName"] = ifname
    info[expconfig["modeminterfacename"]] = ifname
    info["Operator"] = "local"
    info["Timestamp"] = time.time()


def create_meta_process(ifname, expconfig):
    meta_info = Manager().dict()
    process = Process(target=metadata,
                      args=(meta_info, ifname, expconfig, ))
    process.daemon = True
    return (meta_info, process)


def create_exp_process(meta_info, expconfig):
    process = Process(target=run_exp, args=(meta_info, expconfig, ))
    process.daemon = True
    return process


if __name__ == '__main__':
    """The main thread control the processes (experiment/metadata))."""

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
        allowed_interfaces = EXPCONFIG['allowed_interfaces']
        if_without_metadata = EXPCONFIG['interfaces_without_metadata']
        meta_grace = EXPCONFIG['meta_grace']
        exp_grace = EXPCONFIG['exp_grace'] + EXPCONFIG['time']
        ifup_interval_check = EXPCONFIG['ifup_interval_check']
        time_between_experiments = EXPCONFIG['time_between_experiments']
        EXPCONFIG['guid']
        EXPCONFIG['modem_metadata_topic']
        EXPCONFIG['zmqport']
        EXPCONFIG['verbosity']
        EXPCONFIG['resultdir']
    except Exception as e:
        print "Missing expconfig variable {}".format(e)
        raise e

    for ifname in allowed_interfaces:
        # Interface is not up we just skip that one
        if not check_if(ifname):
            if EXPCONFIG['verbosity'] > 1:
                print "Interface is not up {}".format(ifname)
            continue

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
            add_manual_metadata_information(meta_info, ifname)

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
                print "Trying to get meta data"
            time.sleep(ifup_interval_check)

        # Ok we did not get any information within the grace period
        # we give up on that interface
        if not check_meta(meta_info, meta_grace, EXPCONFIG):
            if EXPCONFIG['verbosity'] > 1:
                print "No Metada'nodeid': 'fake.nodeid',ta continuing"
            continue

        # Ok we have some information lets start the experiment script
        if EXPCONFIG['verbosity'] > 1:
            print "Starting experiment"
        start_time_exp = time.time()
        # Create a experiment process and start it
        exp_process = exp_process = create_exp_process(meta_info, EXPCONFIG)
        exp_process.start()

        while (time.time() - start_time_exp < exp_grace and
               exp_process.is_alive()):
            # Here we could add code to handle interfaces going up or down
            # Similar to what exist in the ping experiment
            # However, for now we just abort if we loose the interface

            # No modem information hack to add required information
            if (check_if(ifname) and ifname in if_without_metadata):
                add_manual_metadata_information(meta_info, ifname, EXPCONFIG)

            if not (check_if(ifname) and check_meta(meta_info,
                                                    meta_grace,
                                                    EXPCONFIG)):
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
        time.sleep(time_between_experiments)
    if EXPCONFIG['verbosity'] > 1:
        print ("Interfaces {} "
               "done, existing").format(allowed_interfaces)
