#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date: Sept 2015
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

# CODENAME : Rainbow

r"""
Simple curl wrapper download a url/file using curl.

The output will be formated into a json object suitable for storage in the
MONROE db.
"""
import json
import time
import os
import argparse
import textwrap
from subprocess import check_output, CalledProcessError
import zmq
import sys
from multiprocessing import Process, Manager
import netifaces
import time

CMD_NAME = os.path.basename(__file__)

DEBUG = False
# Configuration
TOPIC = 'MONROE.META.DEVICE.MODEM'
CONFIGFILE = '/monroe/config'
ZMQPORT = 'tcp://172.17.0.1:5556'
IF_META_GRACE = 120  # The grace period to wait for IF metadata
IFUP_INTERVAL_CHECK = 5  # Check if up with this interval (if it is down)
TIME_BETWEEN_EXPERIMENTS = 30  # The time between each interface
DATAVERSION = 1
DATAID = 'MONROE.EXP.HTTP.DOWNLOAD'


# What to save from curl
CURL_METRICS = ('{ '
                '"Host": "%{remote_ip}", '
                '"Port": "%{remote_port}", '
                '"Speed": %{speed_download}, '
                '"Bytes": %{size_download}, '
                '"TotalTime": %{time_total}, '
                '"SetupTime": %{time_starttransfer} '
                '}')


def run_exp(meta_info, exp_config):
    """Run the experiment and collect the output."""
    ifname = meta_info['InterfaceName']
    cmd = ["curl",
           "--raw",
           "--silent",
           "--write-out", "{}".format(CURL_METRICS),
           "--interface", "{}".format(ifname),
           "--max-time", "{}".format(exp_config['time']),
           "--range", "0-{}".format(exp_config['size']),
           "{}".format(exp_config['url'])]
    try:
        output = check_output(cmd)
        # Clean away leading and trailing whitespace
        output = output.strip(' \t\r\n\0')
        # Convert to JSON
        msg = json.loads(output)
        # Should be replaced with real value from "scheduler"/initscript

        msg.update({
            "Guid": exp_config['guid'],
            "TimeStamp": time.time(),
            "Iccid": meta_info["ICCID"],
            "Operator": meta_info["Operator"],
            "DownloadTime": msg["TotalTime"] - msg["SetupTime"],
            "SequenceNumber": 1
        })
        if DEBUG:
            print (msg)
        else:
            monroe_exporter.save_output(msg, DATAID, DATAVERSION)
    except CalledProcessError as e:
        log_str = "Execution failed: {}".format(e)
        print log_str


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

    # Default values
    expconfig = {
            'url': "http://193.10.227.25/test/1000M.zip",
            'size': 3*1024 - 1,
            'time': 3600,
            'allowed_interfaces': ['usb0',
                                   'usb1',
                                   'usb2',
                                   'wlan0',
                                   'wwan2']
            }

    if not DEBUG:
        import monroe_exporter
        # Try to get the experiment config as provided by the scheduler
        try:
            with open(CONFIGFILE) as configfd:
                expconfig.update(json.load(configfd))
                # Stupid way to check so all variables are in place
                expconfig['guid']
                expconfig['size']
                expconfig['time']
                expconfig['allowed_interfaces']
                expconfig['url']
        except Exception as e:
            log_str = "Cannot retrive expconfig {}".format(e)
            print log_str
            raise e
    else:
        expconfig.update({'guid': "Fake.guid.fake"})

    guid = expconfig['guid']
    for ifname in expconfig['allowed_interfaces']:
        # Interface is not up we just skip that one
        if not check_if(ifname):
            continue

        # Create a process for getting the metadata
        # (could have used a thread as well but this is true multiprocessing)
        meta_info, meta_process = create_meta_process(ifname,
                                                      guid,
                                                      TOPIC,
                                                      ZMQPORT)
        meta_process.start()

        # Creat a experiment script
        exp_process = exp_process = create_exp_process(meta_info,
                                                       expconfig)

        log_str = "Starting Experiment Run on if : {}".format(ifname)
        print log_str

        # On these we do net get modem information fugly hack to make it work
        if (check_if(ifname) and
                (ifname is 'wlan0' or
                 ifname is 'eth0')):
            meta_info["InterfaceName"] = ifname
            meta_info["Operator"] = "local"
            meta_info["Timestamp"] = time.time()

        # Get metdata if the process dies we restart it
        start_time = time.time()
        while (time.time() - start_time < IF_META_GRACE and
               not check_meta(meta_info, IF_META_GRACE)):
            if not meta_process.is_alive():
                # This is serious as we will not receive updates
                if exp_process.is_alive():  # Clean up the exp_thread
                    exp.terminate()

                # The dict may have been corrupt so recreate that one
                meta_info, meta_process = create_meta_process(ifname,
                                                              guid,
                                                              TOPIC,
                                                              ZMQPORT)
                meta_process.start()
                exp_process = create_exp_process(meta_info, expconfig)
            print "Trying to get meta data"
            time.sleep(IFUP_INTERVAL_CHECK)

        # Ok we did not get any information within the grace period
        # we give up on that interface
        if not check_meta(meta_info, IF_META_GRACE):
            print "No Metadata continuing"
            continue

        # Ok we have some information lets start the experiment script
        start_time_exp = time.time()

        exp_grace = expconfig['time'] + IF_META_GRACE

        print "Starting experiment"
        exp_process.start()
        while (time.time() - start_time_exp < exp_grace and
               exp_process.is_alive()):
            # Here we could add code to handle interfces going up or down
            # Similar to what exist in the ping experiment
            # For now we just abort if we loose the interface

            # No modem information fugly hack to make it work
            if (check_if(ifname) and
                    (ifname is 'wlan0' or
                     ifname is 'eth0')):
                meta_info["InterfaceName"] = ifname
                meta_info["Operator"] = "wifi"
                meta_info["Timestamp"] = time.time()

            if not (check_if(ifname) and check_meta(meta_info, IF_META_GRACE)):
                print "Interface went down during a experiment"
                break
            elapsed_exp = time.time() - start_time_exp
            print "Running Experiment for {} s".format(elapsed_exp)
            time.sleep(IFUP_INTERVAL_CHECK)

        if exp_process.is_alive():
            exp_process.terminate()
        if meta_process.is_alive():
            meta_process.terminate()

        elapsed = time.time() - start_time
        print "Finished {} after {}".format(ifname, elapsed)
        time.sleep(TIME_BETWEEN_EXPERIMENTS)
    print "All done existing"
