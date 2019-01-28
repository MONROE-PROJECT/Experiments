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
import os
import json
import zmq
import netifaces
import time
import subprocess
from subprocess import check_output, CalledProcessError
from multiprocessing import Process, Manager
from dig_parser import parse_dig
import dig_parser
import socket
from tempfile import NamedTemporaryFile
from os import path
from collections import OrderedDict
import tempfile
import shutil
import traceback
import tarfile


# Configuration
DEBUG = False
CONFIGFILE = '/monroe/config'
RESULTS_DIR = "/monroe/results/"

# Default values (overwritable from the scheduler)
# Can only be updated from the main thread and ONLY before any
# other processes are started
EXPCONFIG = {
        "guid": "no.guid.in.config.file",  # Should be overridden by scheduler
        "url": "http://193.10.227.25/test/1000M.zip",   # AEL: might be worth to keep the curl measurements to see performance against 
                                                        # machines that provide advertisements services
        #"targets": ["www.google.com", "ds.serving-sys.com", "instagramstatic-a.akamaihd.net"], # target for DNS query
        "size": 3*1024,  # The maximum size in Kbytes to download
        "time": 3600,  # The maximum time in seconds for a download
        "zmqport": "tcp://172.17.0.1:5556",
        "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
        "dataversion": 2,
        "dataid": "MONROE.EXP.DIG",
        "nodeid": "fake.nodeid",
        "meta_grace": 120,  # Grace period to wait for interface metadata
        "exp_grace": 120,  # Grace period before killing experiment
        "ifup_interval_check": 5,  # Interval to check if interface is up
        "time_between_experiments": 30,
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "resolvers": ["default"],
        "modeminterfacename": "InternalInterface",
        "disabled_interfaces": ["lo",
                                "metadata",
                                "eth0",
                                "wlan0"
                                ],  # Interfaces to NOT run the experiment on
        "interfaces_without_metadata": ["eth0",
                                        "wlan0"]  # Manual metadata on these IF
        }

def get_filename(data, postfix, ending, tstamp):
    return "{}_{}_{}_{}{}.{}".format(data['nodeid'], data['dataid'], data['dataversion'], tstamp,
        ("_" + postfix) if postfix else "", ending)

def save_output(data, msg, postfix=None, ending="json", tstamp=time.time(), outdir="/monroe/results/"):
    f = NamedTemporaryFile(mode='w+', delete=False, dir=outdir)
    f.write(msg)
    f.close()
    outfile = path.join(outdir, get_filename(data, postfix, ending, tstamp))
    move_file(f.name, outfile)

def move_file(f, t):
    try:
        shutil.move(f, t)
        os.chmod(t, 0o644)
    except:
        traceback.print_exc()

def copy_file(f, t):
    try:
        shutil.copyfile(f, t)
        os.chmod(t, 0o644)
    except:
        traceback.print_exc()

def add_dns(interface):
    str = ""
    try:
        with open('/dns') as dnsfile:

            dnsdata = dnsfile.readlines()
            dnslist = [ x.strip() for x in dnsdata ]
            for item in dnslist:
                if interface in item:
                    str += item.split('@')[0].replace("server=", "nameserver ")
                    str += "\n"
        with open("/etc/resolv.conf", "w") as f:
            f.write(str)
    except:
        print("Could not find DNS file")
    print str
    return str

def run_dig(ifname, target, expconfig, public_ip):
    netifaces.ifaddresses(ifname)
    if_ip = netifaces.ifaddresses(ifname)[netifaces.AF_INET][0]['addr']
    # clientSubnetParameter = "+subnet=" + public_ip.strip() + "/32"

    cmd = [ "dig", "-b", "{}".format(if_ip), target]

    # if (clientSubnetParameter):
    #    cmd.append(clientSubnetParameter)
    # Safeguard to always have a defined output variable
    dig = None
    data = None
    msg = {}
    for resolver in expconfig['resolvers']:
        # need to run the queries for a set of different resolvers
        if (resolver != "default"):
            cmd.append("@" + str(resolver))

        print "Running dig command: " + " ".join([str(element) for element in cmd])
        try:
            start_dig = int(time.time())
            data =  check_output(cmd)
            end_dig = int(time.time())
            if not data:
                dig = {'error': 'no dig output'}
                print "error!! no dig output"
            try:
                 dig = parse_dig(data) 
            except Exception as e:
                 dig = {'error': 'could not parse dig output'}
                 print "error!! could not parse dig output"
            msg[resolver] = dig
            msg[resolver]['Timestamp'] = start_dig
            msg[resolver]['raw'] = data.decode('ascii', 'replace')
        except Exception as e:
            if expconfig['verbosity'] > 0:
                print ("Execution or parsing failed for "
                       "command : {}, "
                       "output : {}, "
                       "error: {}").format(cmd, data, e)
    return msg

def run_exp(meta_info, expconfig):
    """Seperate process that runs the experiment and collect the ouput.

        Will abort if the interface goes down.
    """
    ifname = meta_info[expconfig["modeminterfacename"]]
    if_ip = netifaces.ifaddresses(ifname)[netifaces.AF_INET][0]['addr']
    print "Local IP Address of testing interface is {}.".format(if_ip)
    #if_name = meta_info["InternalInterface"]
    add_dns(if_ip)
    print "selecting DNS servers... resolv/conf overwritten. "
    #nameserver=[socket.gethostbyname('resolver1.opendns.com')][0]
    #get_pub_ip = ['dig', '-b', '{}'.format(if_ip), '+short', 'myip.opendns.com', '@' + str(nameserver)]
    get_pub_ip = ['dig', '-b', '{}'.format(if_ip), '+short', 'myip.opendns.com', '@208.67.222.222']
    print "Getting public IP: " + ' '.join(get_pub_ip)
    try:
        public_ip = check_output(get_pub_ip)
        print "Public IP: " + str(public_ip)
    except:
        public_ip = if_ip # the dig command fired an error
        print "the DIG command to get the public IP had an error! CHECK!! "

    res = {}
    res.update({
            "Guid": expconfig['guid'],
            "DataId": expconfig['dataid'],
            "DataVersion": expconfig['dataversion'],
            "NodeId": expconfig['nodeid'],
            #"Timestamp": start,
            "Iccid": meta_info["ICCID"],
            "Operator": meta_info["Operator"],
            "IMSIMCCMNC":meta_info["IMSIMCCMNC"],
            "NWMCCMNC":meta_info["NWMCCMNC"],
            #"resolver":resolver,
            #"cmd_time":end-start,
            "SequenceNumber": 1,
            "publicIP" : public_ip
        })
    fqdns = open("/opt/monroe/ABP_filters_fqdn_list", 'r+')
    #fqdns = open("/opt/monroe/test_fqdn", 'r+')
    targets = []
    for line in fqdns:
        if line[0]=="#":
            continue
        targets.append(line.strip())
    try:
        start = int(time.time())
        for target in targets: #expconfig['targets']
            res[target] = {}
            res[target] = run_dig(ifname, target, expconfig, public_ip)
        save_output(data=expconfig, msg=json.dumps(res), tstamp=start, outdir=expconfig['resultdir'])
    except Exception as e:
        print e
        #traceback.print_exc()

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
    return (expconfig["modeminterfacename"] in info and
            "Operator" in info and
            "Timestamp" in info and
            time.time() - info["Timestamp"] < graceperiod)


def add_manual_metadata_information(info, ifname, expconfig):
    """Only used for local interfaces that do not have any metadata information.

       Normally eth0 and wlan0.
    """
    info[expconfig["modeminterfacename"]] = ifname
    info["Operator"] = "local"
    info["ICCID"] = "local"
    info["Timestamp"] = time.time()
    info["NWMCCMNC"] = "n/a"
    info["IMSIMCCMNC"] = "n/a"


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
            print e
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
        exp_grace = EXPCONFIG['exp_grace'] + EXPCONFIG['time']
        ifup_interval_check = EXPCONFIG['ifup_interval_check']
        time_between_experiments = EXPCONFIG['time_between_experiments']
        EXPCONFIG['guid']
        EXPCONFIG['modem_metadata_topic']
        EXPCONFIG['zmqport']
        EXPCONFIG['verbosity']
        EXPCONFIG['resultdir']
        EXPCONFIG['modeminterfacename']
    except Exception as e:
        print "Missing expconfig variable {}".format(e)
        raise e
    tot_start_time = time.time()
    print "Measuring on NODE " + str(EXPCONFIG['nodeid'])
    print "available interfaces: " + str(netifaces.interfaces())
    for ifname in netifaces.interfaces():
        # Skip disbaled interfaces
        if ifname in disabled_interfaces:
            if EXPCONFIG['verbosity'] > 1:
                print "Interface is disabled skipping, {}".format(ifname)
            continue

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
            add_manual_metadata_information(meta_info, ifname, EXPCONFIG)

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
            continue

        # Ok we have some information lets start the experiment script
        if EXPCONFIG['verbosity'] > 1:
            print "Starting experiment"
            print ("Operator: " + str(meta_info["Operator"]) +  "IMSIMCCMNC: " +str(meta_info["IMSIMCCMNC"]) + "NWMCCMNC:" + str(meta_info["NWMCCMNC"]))
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
        print ("Complete experiment took {}"
               ", now exiting").format(time.time() - tot_start_time)
