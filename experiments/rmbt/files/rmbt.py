#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Leonhard Wimmer (based on curl_experiment.py by Jonas Karlsson)
# Date: June 2017
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""
Simple wrapper to run rmbt-client.

The script will execute one experiment for each of the allowed_interfaces.
All default values are configurable from the scheduler.
The output will be formated into a json object suitable for storage in the
MONROE db.
"""
import os
import json
import zmq
import netifaces
import time
import tempfile
import shutil
from os import path
from traceroute_parser import parse_traceroute
from subprocess import Popen, PIPE, STDOUT, call
from multiprocessing import Process, Manager
from collections import OrderedDict
from tempfile import NamedTemporaryFile


# Configuration
DEBUG = False
CONFIGFILE = '/monroe/config'

# Default values (overwritable from the scheduler)
# Can only be updated from the main thread and ONLY before any
# other processes are started
EXPCONFIG = {
        # The following value are specific to the monroe platform
        "guid": "no.guid.in.config.file",               # Should be overridden by scheduler
        "zmqport": "tcp://172.17.0.1:5556",
        "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
        "dataversion": 2,
        "dataid": "MONROE.EXP.RMBT",
        "nodeid": "fake.nodeid",
        "meta_grace": 120,                              # Grace period to wait for interface metadata
        "exp_grace": 300,                               # Grace period before killing experiment
        "ifup_interval_check": 3,                       # Interval to check if interface is up
        "time_between_experiments": 0,
        "verbosity": 2,                                 # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "modeminterfacename": "InternalInterface",
        #"require_modem_metadata": {"DeviceMode": 4},   # only run if in LTE (5) or UMTS (4)
        "save_metadata_topic": "MONROE.META",
        "save_metadata_resultdir": None,                # set to a dir to enable saving of metadata
        "add_modem_metadata_to_result": False,          # set to True to add one captured modem metadata to rmbt result
        "traceroute_resultdir": "/monroe/results/",     # set to a dir to enable traceroute before rmbt
        "disabled_interfaces": ["lo",
                                "metadata",
                                "eth0",
                                "wlan0"
                                ],                      # Interfaces to NOT run the experiment on
        #"enabled_interfaces": ["op0"],                 # Interfaces to run the experiment on
        "interfaces_without_metadata": ["eth0",
                                        "wlan0"],       # Manual metadata on these IF

        # These values are specic for this experiment
        # rmbt defaults:
        #"cnf_server_host": "", # REQUIRED PARAMETER
        #"cnf_server_port": ,   # REQUIRED PARAMETER
        "cnf_secret": "",
        "cnf_encrypt": False,
        "cnf_dl_num_flows": 5,
        "cnf_ul_num_flows": 5,
        "cnf_dl_duration_s": 10,
        "cnf_ul_duration_s": 10,
        "cnf_dl_pretest_duration_s": 1,
        "cnf_ul_pretest_duration_s": 1,
        "cnf_rtt_tcp_payload_num": 11,
        "cnf_dl_wait_time_s": 20,
        "cnf_ul_wait_time_s": 20,
        "cnf_timeout_s": 30,
        "cnf_tcp_info_sample_rate_us": 10000, # = 10ms
}

def get_filename(data, postfix, ending, tstamp):
    return "{}_{}_{}_{}{}.{}".format(data['nodeid'], data['dataid'], data['dataversion'], tstamp,
        ("_" + postfix) if postfix else "", ending)

def save_output(data, msg, postfix=None, ending="json", tstamp=time.time(), outdir="/monroe/results/"):
    f = NamedTemporaryFile(delete=False, dir=outdir)
    f.write(msg)
    f.close()
    outfile = path.join(outdir, get_filename(data, postfix, ending, tstamp))
    move_file(f.name, outfile)

def move_file(f, t):
    os.rename(f, t)
    os.chmod(t, 0644)

def run_exp(meta_info, expconfig):
    """Seperate process that runs the experiment and collect the ouput.

        Will abort if the interface goes down.
    """
    output = None
    try:
        cmd = ["rmbt", "-c", "-"]
        p = Popen(cmd, stdin=PIPE, stdout=PIPE)
        output = p.communicate(input=json.dumps(expconfig))[0]

        msg = json.loads(output, object_pairs_hook=OrderedDict)
        msg.update({
            "ErrorCode": p.returncode,
            "Guid": expconfig['guid'],
            "DataId": expconfig['dataid'],
            "DataVersion": expconfig['dataversion'],
            "NodeId": expconfig['nodeid'],
            "Timestamp": expconfig['timestamp'],
            "Iccid": meta_info["ICCID"],
            "Operator": meta_info["Operator"],
            "SequenceNumber": 1
        })
        if expconfig['verbosity'] > 2:
            print(msg)
        if not DEBUG:
            save_output(data=expconfig, msg=json.dumps(msg), tstamp=expconfig['timestamp'], outdir=expconfig['resultdir'])
    except Exception as e:
        if expconfig['verbosity'] > 0:
            print ("Execution or parsing failed for "
                   "command : {}, "
                   "output : {}, "
                   "error: {}").format(cmd, output, e)


def metadata(meta_ifinfo, ifname, expconfig):
    """Seperate process that attach to the ZeroMQ socket as a subscriber.

        Will listen forever to messages with topic defined in topic and update
        the meta_ifinfo dictionary (a Manager dict).
    """
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(expconfig['zmqport'])
    topic = expconfig['modem_metadata_topic']
    do_save = False
    if 'save_metadata_topic' in expconfig and 'save_metadata_resultdir' in expconfig and expconfig['save_metadata_resultdir']:
        topic = expconfig['save_metadata_topic']
        do_save = True
    socket.setsockopt(zmq.SUBSCRIBE, topic.encode('ASCII'))
    # End Attach
    while True:
        data = socket.recv()
        try:
            (topic, msgdata) = socket.recv().split(' ', 1)
            msg = json.loads(msgdata)
            if do_save and not topic.startswith("MONROE.META.DEVICE.CONNECTIVITY."):
                # Skip all messages that belong to connectivity as they are redundant
                # as we save the modem messages.
                msg['nodeid'] = expconfig['nodeid']
                msg['dataid'] = msg['DataId']
                msg['dataversion'] = msg['DataVersion']
                tstamp = time.time()
                if 'Timestamp' in msg:
                    tstamp = msg['Timestamp']
                if expconfig['verbosity'] > 2:
                    print(msg)
                save_output(data=msg, msg=json.dumps(msg), tstamp=tstamp, outdir=expconfig['save_metadata_resultdir'])

            if topic.startswith(expconfig['modem_metadata_topic']):
                if (expconfig["modeminterfacename"] in msg and
                        msg[expconfig["modeminterfacename"]] == ifname):
                    # In place manipulation of the reference variable
                    for key, value in msg.iteritems():
                        meta_ifinfo[key] = value
        except Exception as e:
            if expconfig['verbosity'] > 0:
                print ("Cannot get metadata in container: {}"
                       ", {}").format(e, expconfig['guid'])
            pass


# Helper functions
def check_if(ifname):
    """Check if interface is up and have got an IP address."""
    return (ifname in netifaces.interfaces() and
            netifaces.AF_INET in netifaces.ifaddresses(ifname))

def get_ip(ifname):
    """Get IP address of interface."""
    # TODO: what about AFINET6 / IPv6?
    return netifaces.ifaddresses(ifname)[netifaces.AF_INET][0]['addr']

def check_meta(info, graceperiod, expconfig):
    """Check if we have recieved required information within graceperiod."""
    if not (expconfig["modeminterfacename"] in info and
            "Operator" in info and
            "Timestamp" in info and
            time.time() - info["Timestamp"] < graceperiod):
        return False
    if not "require_modem_metadata" in expconfig:
        return True
    for k,v in expconfig["require_modem_metadata"].items():
        if k not in info:
            if expconfig['verbosity'] > 0:
                print("Got metadata but key '{}' is missing".format(k))
            return False
        if not info[k] == v:
            if expconfig['verbosity'] > 0:
                print("Got metadata but '{}'='{}'; expected: '{}''".format(k, info[k], v))
            return False
    return True

def add_manual_metadata_information(info, ifname, expconfig):
    """Only used for local interfaces that do not have any metadata information.

       Normally eth0 and wlan0.
    """
    info[expconfig["modeminterfacename"]] = ifname
    info["Operator"] = "local"
    info["ICCID"] = "local"
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

def traceroute(target, interface, outputfile):
    cmd = ['traceroute', '-A']
    if (interface):
        cmd.extend(['-i', interface])
    cmd.append(target)
    if EXPCONFIG['verbosity'] > 1:
        print("doing traceroute...")
    time_start = time.time()
    p = Popen(cmd, stdout=PIPE)
    data = p.communicate()[0]
    time_end = time.time()
    if EXPCONFIG['verbosity'] > 1:
        print("traceroute finished.")
    if EXPCONFIG['verbosity'] > 2:
        print("traceroute: {}".format(data))
    try:
        traceroute = parse_traceroute(data)
    except Exception as e:
        traceroute = {'error': 'could not parse traceroute'}
    traceroute['time_start'] = time_start
    traceroute['time_end'] = time_end
    traceroute['raw'] = data
    with open(outputfile, 'w') as f:
        f.write(json.dumps(traceroute))

if __name__ == '__main__':
    """The main thread control the processes (experiment/metadata))."""

    if not DEBUG:
        # Try to get the experiment config as provided by the scheduler
        try:
            with open(CONFIGFILE) as configfd:
                EXPCONFIG.update(json.load(configfd))
        except Exception as e:
            print("Cannot retrive expconfig {}".format(e))
            raise e
    else:
        # We are in debug state always put out all information
        EXPCONFIG['verbosity'] = 3
        try:
            EXPCONFIG['disabled_interfaces'].remove("eth0")
        except Exception as e:
            pass

    # Short hand variables and check so we have all variables we need
    try:
        disabled_interfaces = EXPCONFIG['disabled_interfaces']
        if_without_metadata = EXPCONFIG['interfaces_without_metadata']
        meta_grace = EXPCONFIG['meta_grace']
        exp_grace = EXPCONFIG['exp_grace']
        ifup_interval_check = EXPCONFIG['ifup_interval_check']
        time_between_experiments = EXPCONFIG['time_between_experiments']
        EXPCONFIG['guid']
        EXPCONFIG['modem_metadata_topic']
        EXPCONFIG['zmqport']
        EXPCONFIG['verbosity']
        EXPCONFIG['resultdir']
        EXPCONFIG['modeminterfacename']
    except Exception as e:
        print("Missing expconfig variable {}".format(e))
        raise e

    # enable flows and stats by default:
    temp_flows_json = None
    temp_stats_json = None
    if 'cnf_file_flows' not in EXPCONFIG:
        EXPCONFIG['cnf_file_flows'] = temp_flows_json = path.join(EXPCONFIG['resultdir'], "tmpflows.json.xz")
    if 'cnf_file_stats' not in EXPCONFIG:
        EXPCONFIG['cnf_file_stats'] = temp_stats_json = path.join(EXPCONFIG['resultdir'], "tmpstats.json.xz")

    tot_start_time = time.time()
    for ifname in netifaces.interfaces():
        # Skip disbaled interfaces
        if ifname in disabled_interfaces:
            if EXPCONFIG['verbosity'] > 1:
                print("Interface is disabled, skipping {}".format(ifname))
            continue

        if 'enabled_interfaces' in EXPCONFIG and not ifname in EXPCONFIG['enabled_interfaces']:
            if EXPCONFIG['verbosity'] > 1:
                print("Interface is not enabled, skipping {}".format(ifname))
            continue

        # Interface is not up we just skip that one
        if not check_if(ifname):
            if EXPCONFIG['verbosity'] > 1:
                print("Interface is not up {}".format(ifname))
            continue

        EXPCONFIG['cnf_bind_ip'] = get_ip(ifname)

        # Create a process for getting the metadata
        # (could have used a thread as well but this is true multiprocessing)
        meta_info, meta_process = create_meta_process(ifname, EXPCONFIG)
        meta_process.start()

        if EXPCONFIG['verbosity'] > 1:
            print("Starting Experiment Run on if : {}".format(ifname))

        # On these Interfaces we do net get modem information so we hack
        # in the required values by hand whcih will immeditaly terminate
        # metadata loop below
        if (check_if(ifname) and ifname in if_without_metadata):
            add_manual_metadata_information(meta_info, ifname, EXPCONFIG)

        # Run traceroute if requested
        temp_traceroute = None
        if EXPCONFIG['traceroute_resultdir']:
            temp_traceroute = path.join(EXPCONFIG['resultdir'], "tmptraceroute.json")
            traceroute(EXPCONFIG['cnf_server_host'], ifname, temp_traceroute)

        # Try to get metadata
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
                print("Trying to get metadata")
            time.sleep(ifup_interval_check)

        # Ok we did not get any information within the grace period
        # we give up on that interface
        if not check_meta(meta_info, meta_grace, EXPCONFIG):
            if EXPCONFIG['verbosity'] > 1:
                print("No Metadata continuing")
            continue

        # Add metadata if requested
        if EXPCONFIG['add_modem_metadata_to_result']:
            if 'cnf_add_to_result' not in EXPCONFIG:
                EXPCONFIG['cnf_add_to_result'] = {}
            for k,v in meta_info.items():
                EXPCONFIG['cnf_add_to_result']['info_meta_modem_' + k] = v

        # Ok we have some information lets start the experiment script
        if EXPCONFIG['verbosity'] > 1:
            print("Starting experiment")
        EXPCONFIG['timestamp'] = start_time_exp = time.time()
        # Create a experiment process and start it
        exp_process = create_exp_process(meta_info, EXPCONFIG)
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
                    print("Interface went down during a experiment")
                break
            elapsed_exp = time.time() - start_time_exp
            if EXPCONFIG['verbosity'] > 1:
                print("Running Experiment for {} s".format(elapsed_exp))
            time.sleep(ifup_interval_check)

        if exp_process.is_alive():
            exp_process.terminate()
        if meta_process.is_alive():
            meta_process.terminate()

        if temp_flows_json:
            move_file(temp_flows_json, path.join(EXPCONFIG['resultdir'], get_filename(EXPCONFIG, 'FLOWS', 'json.xz', start_time_exp)))
        if temp_stats_json:
            move_file(temp_stats_json, path.join(EXPCONFIG['resultdir'], get_filename(EXPCONFIG, 'STATS', 'json.xz', start_time_exp)))
        if temp_traceroute:
            move_file(temp_traceroute, path.join(EXPCONFIG['resultdir'], get_filename(EXPCONFIG, 'TRACEROUTE', 'json', start_time_exp)))

        elapsed = time.time() - start_time
        if EXPCONFIG['verbosity'] > 1:
            print("Finished {} after {}".format(ifname, elapsed))
        time.sleep(time_between_experiments)
    if EXPCONFIG['verbosity'] > 1:
        print("Complete experiment took {}"
               ", now exiting").format(time.time() - tot_start_time)
