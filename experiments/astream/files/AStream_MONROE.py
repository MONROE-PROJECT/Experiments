#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Andra Lutu, Jonas Karlsson
# Date: October 2016
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""
Simple experiment template to collect metdata and run an experiment.

The script will execute a experiment (DASH player -- AStream) on a interface with a specified
operator and log the gps position during the experiment.
The output will be formated into a json object.

The experiment received the target MPD file and the number of segments to download.
"""
import json
import zmq
import sys
import netifaces
import time
from subprocess import check_output
from multiprocessing import Process, Manager
import dash_client
from dash_client import *
from configure_log_file import configure_log_file, write_json
import config_dash
import dash_buffer
from adaptation import basic_dash, basic_dash2, weighted_dash, netflix_dash
from adaptation.adaptation import WeightedMean

# Constants
DEFAULT_PLAYBACK = 'BASIC'
DOWNLOAD_CHUNK = 1024

# Globals for arg parser with the default values
# Not sure if this is the correct way ....
MPD = "http://128.39.37.161:8080/BigBuckBunny_4s.mpd"
LIST = False
PLAYBACK = DEFAULT_PLAYBACK
DOWNLOAD = False
SEGMENT_LIMIT = 10


# Configuration
DEBUG = False
CONFIGFILE = '/monroe/config'

# Default values (overwritable from the scheduler)
# Can only be updated from the main thread and ONLY before any
# other processes are started
EXPCONFIG = {
        # The following value are specific to the monore platform
        "guid": "no.guid.in.config.file",  # Overridden by scheduler
        "nodeid": "no.nodeid.in.config.file",  # Overridden by scheduler
        "storage": 104857600,  # Overridden by scheduler
        "traffic": 104857600,  # Overridden by scheduler
        "zmqport": "tcp://172.17.0.1:5556",
        "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
        "gps_metadata_topic": "MONROE.META.DEVICE.GPS",
        "dataversion": 1,  #  Version of experiment
        "dataid": "MONROE.EXP.DASH.ASTREAM",  #  Name of experiement
        "nodeid": "fake.nodeid",
        "meta_grace": 120,  # Grace period to wait for interface metadata
        "exp_grace": 120,  # Grace period before killing experiment
        "meta_interval_check": 5,  # Interval to check if interface is up
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "modeminterfacename": "InternalInterface",
        "allowed_interfaces": ["op0",
                               "op1",
                               "op2",
                               "wlan0",
                               "wwan2"],  # Interfaces to run the experiment on
        "interfaces_without_metadata": ["eth0",
                                        "wlan0"]  # Manual metadata on these IF
        }


def run_exp(meta_info, expconfig, dp_object, domain, playback_type=None, download=False, video_segment_duration=None):
    """Seperate process that runs the experiment and collects the ouput.
        Will abort if the interface goes down.
        -- this essentially upgrades the start_playback_smart() function
        Run the DASH client from command line:
        python dash_client.py -m http://128.39.37.161:8080/BigBuckBunny_4s.mpd -n 20
        
    """
    ifname = meta_info['modem']['InternalInterface']
    # AEL - instead of curl, we run the AStream client -- dash_client.py
    
    try:
        # If multiple GPS events have ben registered we take the last one
        start_gps_pos = len(meta_info['gps']) - 1
        # output = check_output(cmd)
        # start the DASH player, according to the selected playback_type
        # dash_client.start_playback_smart(dp_object, domain, playback_type, download, video_segment_duration)

        if "all" in playback_type.lower():
            if mpd_file:
                config_dash.LOG.critical("Start ALL Parallel PLayback")
                start_playback_all(dp_object, domain)
        elif "basic" in playback_type.lower():
            config_dash.LOG.critical("Started Basic-DASH Playback")
            start_playback_smart(dp_object, domain, "BASIC", download, video_segment_duration)
        elif "sara" in playback_type.lower():
            config_dash.LOG.critical("Started SARA-DASH Playback")
            start_playback_smart(dp_object, domain, "SMART", download, video_segment_duration)
        elif "netflix" in playback_type.lower():
            config_dash.LOG.critical("Started Netflix-DASH Playback")
            start_playback_smart(dp_object, domain, "NETFLIX", download, video_segment_duration)
        else:
            config_dash.LOG.error("Unknown Playback parameter {}".format(playback_type))
            return None


        if ifname != meta_info['modem']['InternalInterface']:
            print "Error: Interface has changed during the experiment, abort"
            return
        # We store all gps_positions during the experiment
        gps_positions = meta_info['gps'][start_gps_pos:]

        # # Clean away leading and trailing whitespace
        # output = output.strip(' \t\r\n\0')
        # # Convert to JSON
        # msg = json.loads(output)

        scriptname = expconfig['script'].replace('/', '.')
        dataid = expconfig.get('dataid', scriptname)
        dataversion = expconfig.get('dataversion', 1)

        # To use monroe_exporter the following fields must be present
        # "Guid"
        # "DataId"
        # "DataVersion"
        # "NodeId"
        # "SequenceNumber"

        config_dash.JSON_HANDLE['MONROE'] = {
            "Guid": expconfig['guid'],
            "DataId": dataid,
            "DataVersion": dataversion,
            "NodeId": expconfig['nodeid'],
            "Timestamp": time.time(),
            "Iccid": meta_info['modem']["ICCID"], # modify to MCCMNC from SIM
            "InterfaceName": ifname,
            "Operator": meta_info['modem']["Operator"],
            "SequenceNumber": 1,
            "GPSPositions": gps_positions
        }
    except Exception as e:
        if expconfig['verbosity'] > 0:
            config_dash.LOG.info("MONROE - Execution or parsing failed")
            config_dash.LOG.error(e)


    while dash_player.playback_state not in dash_buffer.EXIT_STATES:
        time.sleep(1)
    write_json()
    if not download:
        clean_files(file_identifier)
    if expconfig['verbosity'] > 1:
        config_dash.LOG.info("MONROE - Finished Experiment")


def metadata(meta_info, expconfig):
    """Seperate process that attach to the ZeroMQ socket as a subscriber.

        Will listen forever to messages with topic defined in topic and update
        the meta_ifinfo dictionary (a Manager dict).
    """
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(expconfig['zmqport'])
    socket.setsockopt(zmq.SUBSCRIBE, bytes(expconfig['modem_metadata_topic']))
    socket.setsockopt(zmq.SUBSCRIBE, bytes(expconfig['gps_metadata_topic']))

    while True:
        data = socket.recv()
        try:
            topic = data.split(" ", 1)[0]
            msg = json.loads(data.split(" ", 1)[1])
            if topic.startswith(expconfig['modem_metadata_topic']):
                if msg['Operator'] == expconfig['operator']:
                    if expconfig['verbosity'] > 2:
                        print ("Got a modem message"
                               " for {}, using"
                               " interface {}").format(msg['Operator'],
                                                       msg['InterfaceName'])
                    # In place manipulation of the refrence variable
                    for key, value in msg.iteritems():
                        meta_info['modem'][key] = value
            if topic.startswith(expconfig['gps_metadata_topic']):
                if expconfig['verbosity'] > 2:
                    print ("Got a gps message "
                           "with seq nr {}").format(msg["SequenceNumber"])
                meta_info['gps'].append(msg)

            if expconfig['verbosity'] > 2:
                print "zmq message", topic, msg
        except Exception as e:
            if expconfig['verbosity'] > 0:
                print ("Cannot get metadata in template container {}"
                       ", {}").format(e, expconfig['guid'])
            pass


# Helper functions
def check_if(ifname):
    """Checks if "internal" interface is up and have got an IP address.

       This check is to ensure that we have an interface in the experiment
       container and that we have a internal IP address.
    """
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
    info["Timestamp"] = time.time()


def create_meta_process(ifname, expconfig):
    meta_info = Manager().dict()
    process = Process(target=metadata,
                      args=(meta_info, ifname, expconfig, ))
    process.daemon = True
    return (meta_info, process)


def create_exp_process(meta_info, expconfig, dp_object, domain, playback_type=None, download=False, video_segment_duration=None):
    """Creates the experiment process."""
    process = Process(target=run_exp, args=(meta_info, expconfig, dp_object, domain, playback_type, download, video_segment_duration, ))
    process.daemon = True
    process.start()
    return process


if __name__ == '__main__':
    """The main thread control the processes (experiment/metadata))."""

    """ Main AStream + MONROE Program wrapper """
    # configure the log file
    # Create arguments
    #parser = ArgumentParser(description='Process Client parameters')
    #create_arguments(parser)
    #args = parser.parse_args()
    #globals().update(vars(args))
    configure_log_file(playback_type=PLAYBACK.lower())
    config_dash.JSON_HANDLE['playback_type'] = PLAYBACK.lower()
    if not MPD:
        print "ERROR: Please provide the URL to the MPD file. Try Again.."
        #return None
        sys.exit(1)
    config_dash.LOG.info('Downloading MPD file %s' % MPD)
    # Retrieve the MPD files for the video
    mpd_file = get_mpd(MPD)
    domain = get_domain_name(MPD)
    dp_object = DashPlayback()
    # Reading the MPD file created
    dp_object, video_segment_duration = read_mpd.read_mpd(mpd_file, dp_object)
    config_dash.LOG.info("The DASH media has %d video representations" % len(dp_object.video))
    if LIST:
        # Print the representations and EXIT
        print_representations(dp_object)
        sys.exit(1)
        #return None


# MONROE stuff
    if not DEBUG:
        import monroe_exporter
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
        EXPCONFIG['modeminterfacename']
    except Exception as e:
        print "Missing expconfig variable {}".format(e)
        raise e

    for ifname in allowed_interfaces:
        # Interface is not up we just skip that one
        if not check_if(ifname):
            if EXPCONFIG['verbosity'] > 1:
                print "Interface is not up {}".format(ifname)
            continue
        # set the default route
            

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
                print "Trying to get metadata"
            time.sleep(ifup_interval_check)

        # Ok we did not get any information within the grace period
        # we give up on that interface
        if not check_meta(meta_info, meta_grace, EXPCONFIG):
            if EXPCONFIG['verbosity'] > 1:
                print "No Metadata continuing"
            continue

        # Ok we have some information lets start the experiment script


        cmd1=["route",
             "del",
             "default"]
        #os.system(bashcommand)
        try:
                check_output(cmd1)
        except CalledProcessError as e:
                if e.returncode == 28:
                        print "Time limit exceeded"
        gw_ip="192.168."+str(meta_info["InternalIPAddress"].split(".")[2])+".1"
        cmd2=["route", "add", "default", "gw", gw_ip,str(ifname)]
        try:
                check_output(cmd2)
        except CalledProcessError as e:
                 if e.returncode == 28:
                        print "Time limit exceeded"
        cmd3=["ip", "route", "get", "8.8.8.8"]
        try:
                output=check_output(cmd3)
        except CalledProcessError as e:
                 if e.returncode == 28:
                        print "Time limit exceeded"
        output = output.strip(' \t\r\n\0')
        output_interface=output.split(" ")[4]
        if output_interface==str(ifname):
                print "Source interface is set to "+str(ifname)

        if EXPCONFIG['verbosity'] > 1:
            print "Starting experiment"
        

        for index in range(len(url_list)):
            for run in range(start_count, loop):
                # Create a experiment process and start it
                start_time_exp = time.time()
                exp_process = exp_process = create_exp_process(meta_info, EXPCONFIG, url_list[index],run+1)
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
               "done, exiting").format(allowed_interfaces)
