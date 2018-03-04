#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Cise Midoglu (based on curl_experiment.py by Jonas Karlsson)
# Date: February 2017
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""
Simple wrapper to run the MONROE-AStream client.

The script will execute one experiment for each of the enabled_interfaces.
All default values are configurable from the scheduler.
The output will be formated into a JSON object suitable for storage in the
MONROE database.
"""

import io
import json
import zmq
import sys
import netifaces
import time
from subprocess import check_output, CalledProcessError
from multiprocessing import Process, Manager
import dash_client
from configure_log_file import configure_log_file, write_json
import config_dash
from dash_buffer import *
from adaptation import basic_dash, basic_dash2, weighted_dash, netflix_dash
from adaptation.adaptation import WeightedMean
import shutil
from tempfile import NamedTemporaryFile
import glob
import numpy
import pandas

# Configuration
DEBUG = False
CONFIGFILE = '/monroe/config'

DEFAULT_MPD = None
DEFAULT_HOST = None
DEFAULT_PORT = None
CONTAINER_VERSION = 'v2.2' #CM: version by Cise Midoglu

#CM: version information
#v2.0   (CM) initial working version including summary statistics
#v2.1   (CM) fixes on summary output, download option
#v2.2   (CM) fix on DEBUG mode, lightweight version vs. full version
#v2.3   (CM) increased default exp_grace

# Default values (overwritable from the scheduler)
# Can only be updated from the main thread and ONLY before any
# other processes are started
EXPCONFIG = {
    # The following value are specific to the monroe platform
    "guid": "no.guid.in.config.file",               # Should be overridden by scheduler
    "zmqport": "tcp://172.17.0.1:5556",
    "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
    "dataversion": 2,
    "dataid": "MONROE.EXP.ASTREAM",
    "nodeid": "local.nodeid",
    "meta_grace": 120,                              # Grace period to wait for interface metadata
    "exp_grace": 10000,                               # Grace period before killing experiment
    "ifup_interval_check": 3,                       # Interval to check if interface is up
    "time_between_experiments": 0,
    "verbosity": 3,                                 # 0 = "Mute", 1=error, 2=Information, 3=verbose
    "resultdir": "/monroe/results/",
    "modeminterfacename": "InternalInterface",
    #"require_modem_metadata": {"DeviceMode": 4},   # only run if in LTE (5) or UMTS (4)
    "save_metadata_topic": "MONROE.META",
    "save_metadata_resultdir": None,                # set to a dir to enable saving of metadata
    "add_modem_metadata_to_result": False,          # set to True to add one captured modem metadata to nettest result
    "disabled_interfaces": ["lo",
                            "metadata"
                            ],                      # Interfaces to NOT run the experiment on
    "enabled_interfaces": ["op0","op1","op2"],                 # Interfaces to run the experiment on
    "interfaces_without_metadata": ["eth0",
                                    "wlan0"],       # Manual metadata on these IF
    "timestamp": time.gmtime(),
    # These values are specific for this experiment
    "cnf_astream_download": False,
    "cnf_astream_download_directory": "videos",
    "cnf_astream_mpd": DEFAULT_MPD,
    "cnf_astream_video": "BigBuckBunny",
    "cnf_astream_segment_duration": 4,
    "cnf_astream_segment_limit": 100,
    "cnf_astream_playback": 'BASIC',
    "cnf_astream_server_host": DEFAULT_HOST,
    "cnf_astream_server_port": DEFAULT_PORT,
    "cnf_astream_tag": None,
    "cnf_astream_wait_btw_algorithms_s": 20,        # Time to wait between different algorithms
    "cnf_astream_compress_additional_results": True,# Whether or not to tar additional log files
    "cnf_astream_q1": 25,
    "cnf_astream_q2": 50,
    "cnf_astream_q3": 75,
    "cnf_astream_q4": 90,

    "cnf_astream_out_fields": 'res_astream_available_bitrates,res_astream_bitrate_mean,res_astream_bitrate_max,res_astream_bitrate_min,\
res_astream_bitrate_q1,res_astream_bitrate_q2,res_astream_bitrate_q3,res_astream_bitrate_q4,\
res_astream_buffer_mean,res_astream_buffer_max,res_astream_buffer_min,\
res_astream_buffer_q1,res_astream_buffer_q2,res_astream_buffer_q3,res_astream_buffer_q4,\
res_astream_numstalls,\
res_astream_durstalls_mean,res_astream_durstalls_max,res_astream_durstalls_min,\
res_astream_durstalls_q1,res_astream_durstalls_q2,res_astream_durstalls_q3,res_astream_durstalls_q4,\
res_astream_durstalls_total,\
res_astream_numswitches_up,res_astream_numswitches_down'

}

# CM: helper functions

def get_filename(data, postfix, ending, tstamp, interface):
    return "{}_{}_{}_{}_{}_{}{}.{}".format(data['dataid'], data['cnf_astream_video'], data['cnf_astream_playback'].lower(), data['nodeid'], interface, tstamp,
        ("_" + postfix) if postfix else "", ending)

def get_prefix(data, postfix, tstamp, interface):
    return "{}_{}_{}_{}_{}_{}{}".format(data['dataid'], data['cnf_astream_video'], data['cnf_astream_playback'].lower(), data['nodeid'], interface, tstamp,
        ("_" + postfix) if postfix else "")

def save_output(data, msg, postfix=None, ending='json', tstamp=time.time(), outdir='/monroe/results/', interface='interface'):
    f = NamedTemporaryFile(mode='w+', delete=False, dir=outdir)
    f.write(msg)
    f.close()
    outfile = os.path.join(outdir, get_filename(data, postfix, ending, tstamp, interface))
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
        data = socket.recv_string()
        try:
            (topic, msgdata) = data.split(' ', 1)
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
                    for key, value in msg.items():
                        meta_ifinfo[key] = value
        except Exception as e:
            if expconfig['verbosity'] > 0:
                print ("Cannot get metadata in container: {}"
                       ", {}").format(e, expconfig['guid'])
            pass

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
    info["Operator"] = "local.operator"
    info["ICCID"] = "local.iccid"
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

#CM: main functions

def run_exp(meta_info, expconfig):
    """Seperate process that runs the experiment and collect the ouput.
        Will abort if the interface goes down.
    """

    cfg = expconfig.copy()
    output = None

    try:
        if 'cnf_add_to_result' not in cfg:
            cfg['cnf_add_to_result'] = {}

        cfg['cnf_add_to_result'].update({
            "Guid": cfg['guid'],
            "DataId": cfg['dataid'],
            "DataVersion": cfg['dataversion'],
            "NodeId": cfg['nodeid'],
            "Time": time.strftime('%Y%m%d-%H%M%S',cfg['timestamp']),
            "Interface": cfg['modeminterfacename'],
            "cnf_astream_mpd": cfg['cnf_astream_mpd'],
            "cnf_astream_server_host": cfg['cnf_astream_server_host'],
            "cnf_astream_server_port": cfg['cnf_astream_server_port'],
            "cnf_astream_playback": cfg['cnf_astream_playback'],
            "cnf_astream_segment_limit": cfg['cnf_astream_segment_limit'],
            "cnf_astream_download": cfg['cnf_astream_download'],
            "cnf_astream_video": cfg['cnf_astream_video'],
            "cnf_astream_tag": cfg['cnf_astream_tag'],
            "cnf_astream_q1": cfg['cnf_astream_q1'],
            "cnf_astream_q2": cfg['cnf_astream_q2'],
            "cnf_astream_q3": cfg['cnf_astream_q3'],
            "cnf_astream_q4": cfg['cnf_astream_q4'],
            "ContainerVersion": CONTAINER_VERSION,
            "DEBUG": DEBUG
            })

        if 'ICCID' in meta_info:
            cfg['cnf_add_to_result']['Iccid'] = meta_info['ICCID']
        if 'Operator' in meta_info:
            cfg['cnf_add_to_result']['Operator'] = meta_info['Operator']
        if 'IMSIMCCMNC' in meta_info:
            cfg['cnf_add_to_result']['IMSIMCCMNC'] = meta_info['IMSIMCCMNC']
        if 'NWMCCMNC' in meta_info:
            cfg['cnf_add_to_result']['NWMCCMNC'] = meta_info['NWMCCMNC']

        # Add metadata if requested
        if cfg['add_modem_metadata_to_result']:

            for k,v in meta_info.items():
                cfg['cnf_add_to_result']['info_meta_modem_' + k] = v

        towrite_data = cfg['cnf_add_to_result']
        ifname = meta_info[cfg['modeminterfacename']]
        towrite_data['Interface']=ifname

        #CM: constructing filename prefix and output directory
        prefix_timestamp=time.strftime('%Y%m%d-%H%M%S',cfg['timestamp'])
        prefix_astream=get_prefix(data=cfg, postfix=None, tstamp=prefix_timestamp, interface=ifname)

        resultdir=cfg['resultdir']
        resultdir_astream=resultdir+'astream/'
        resultdir_astream_video = resultdir_astream + cfg['cnf_astream_download_directory']+ '/'
        if not os.path.exists(resultdir_astream_video):
            os.makedirs(resultdir_astream_video)


        if cfg['verbosity'] > 2:
            print('\n-----------------------------')
            print('DBG: AStream prefix: '+prefix_astream)
            print('DBG: result directory: '+resultdir_astream)
            print('DBG: result directory (videos): '+resultdir_astream_video)
            print('-----------------------------')

        #CM: running AStream
        try:

            if cfg['verbosity'] > 1:
                print('\n-----------------------------')
                print('DBG: running MONROE-AStream')
                print('-----------------------------')

            run_astream(cfg['cnf_astream_mpd'],cfg['cnf_astream_server_host'],cfg['cnf_astream_server_port'],cfg['cnf_astream_video'],cfg['cnf_astream_playback'],cfg['cnf_astream_segment_limit'],cfg['cnf_astream_download'],resultdir_astream_video)

        except Exception as e:
            if cfg['verbosity'] > 0:
                print ('[Exception #2] Execution or parsing failed for error: {}').format(e)

        #CM: checking results
        astream_segment_log = glob.glob(resultdir_astream+'ASTREAM*.json')[0]
        astream_buffer_log = glob.glob(resultdir_astream+'DASH_BUFFER*.csv')[0]
        astream_runtime_log = glob.glob(resultdir_astream+'DASH_RUNTIME*.log')[0]

        if cfg['verbosity'] > 2:
            print('\n-----------------------------')
            print('DBG: output files from AStream core:')
            print(astream_segment_log)
            print(astream_buffer_log)
            print(astream_runtime_log)
            print('-----------------------------')

        #CM: generating summary output
        out_astream = None

        if not DEBUG:
            try:
                out_astream = getOutput(astream_segment_log,astream_buffer_log,cfg['cnf_astream_q1'],cfg['cnf_astream_q2'],cfg['cnf_astream_q3'],cfg['cnf_astream_q4'],cfg['cnf_astream_segment_duration'])

                if out_astream is not None:
                    if cfg['verbosity'] > 2:
                        print('\n-----------------------------')
                        print('DBG: AStream summary:')
                        print(out_astream)
                        print('-----------------------------')

                    out_astream_fields = out_astream.split(',')
                    summary_astream_fields = cfg['cnf_astream_out_fields'].split(',')

                    if len(out_astream_fields) == len(summary_astream_fields):
                        for i in xrange(0,len(summary_astream_fields)-1):
                            towrite_data[summary_astream_fields[i]]=out_astream_fields[i]
                    else:
                        for i in xrange(0,len(summary_astream_fields)-1):
                            towrite_data[summary_astream_fields[i]]='NA'

            except Exception as e:
                if cfg['verbosity'] > 0:
                    print ('[Exception #3] Execution or parsing failed for error: {}').format(e)

        if cfg['verbosity'] > 1:
            print('\n-----------------------------')
            print('DBG: saving results')
            print('-----------------------------')

        #CM: compressing all outputs other than summary JSON
        if 'cnf_astream_compress_additional_results' in cfg and cfg['cnf_astream_compress_additional_results']:
            foldername_zip=get_filename(data=cfg, postfix=None, ending="extra", tstamp=prefix_timestamp, interface=ifname)
            basename_zip=os.path.join(resultdir,foldername_zip)
            #print(foldername_zip)

            shutil.move(resultdir_astream,basename_zip)
            shutil.make_archive(base_name=basename_zip, format='gztar', root_dir=resultdir, base_dir=foldername_zip)#"./")
            shutil.rmtree(basename_zip)

        save_output(data=cfg, msg=json.dumps(towrite_data), postfix="summary", tstamp=prefix_timestamp, outdir=cfg['resultdir'], interface=ifname)

    except Exception as e:
        if cfg['verbosity'] > 0:
            print ('[Exception #1] Execution or parsing failed for error: {}').format(e)

def run_astream(mpd,server_host,server_port,video,algorithm,segment_limit,download,directory):

    if mpd is not None:
        dash_client.main(mpd,algorithm,segment_limit,download,directory)
    else:
        mpd_url = 'http://' + server_host + ':' + str(server_port) + '/' + video + '.mpd'
        dash_client.main(mpd_url,algorithm,segment_limit,download,directory)

def getOutput(segmentlog,bufferlog,q1,q2,q3,q4,segmentduration):
    out = calculateBitrate(segmentlog,q1,q2,q3,q4) + ',' + calculateBuffer(bufferlog,q1,q2,q3,q4,segmentduration) + ',' + calculateStallings(segmentlog,q1,q2,q3,q4)
    return out

def calculateBitrate(segmentlog,q1,q2,q3,q4):

    try:
        bitrates=[]
        json_in = open(segmentlog)
        clientlog=json.load(json_in)
        #playback_info = clientlog["playback_info"]
        #down_shifts = playback_info["down_shifts"]
        #up_shifts = playback_info["up_shifts"]
        segment_info = clientlog["segment_info"]
        for segment in segment_info:
            #print segment
            if 'init' not in segment[0]:
                bitrates.append(segment[1]/1000)
                #print segment[0], segment[1]

        bitrates_avg=numpy.mean(bitrates)
        bitrates_max=max(bitrates)
        bitrates_min=min(bitrates)
        bitrates_q1=numpy.percentile(bitrates, q1)
        bitrates_q2=numpy.percentile(bitrates, q2)
        bitrates_q3=numpy.percentile(bitrates, q3)
        bitrates_q4=numpy.percentile(bitrates, q4)

        video_metadata = clientlog["video_metadata"]
        available_bitrates = video_metadata["available_bitrates"]

        bitrates_list=''
        for available_bitrate in available_bitrates:
            try:
                bitrate_current = str(available_bitrate["bandwidth"])
            except Exception:
                #CM: bitrates list is not a dictionary
                bitrate_current = str(available_bitrate)

            bitrates_list = bitrates_list + 'b' + bitrate_current + ' '

        #print (bitrates_list + ',' + str(bitrates_avg) + ',' + str(bitrates_max) + ',' + str(bitrates_min) + ',' + str(bitrates_q1) + ',' + str(bitrates_q2) + ',' + str(bitrates_q3) + ',' + str(bitrates_q4))
        return bitrates_list + ',' + str(bitrates_avg) + ',' + str(bitrates_max) + ',' + str(bitrates_min) + ',' + str(bitrates_q1) + ',' + str(bitrates_q2) + ',' + str(bitrates_q3) + ',' + str(bitrates_q4)

    except Exception as e:
        print ('[ERROR] AStream calculateBitrate exception: {}').format(e)
        return 'NA,NA,NA,NA,NA,NA,NA,NA'

def calculateBuffer(bufferlog,q1,q2,q3,q4,segmentduration):

    try:
        csvfile = pandas.read_csv(bufferlog)
        epoch_time = csvfile.EpochTime
        current_playback_time = csvfile.CurrentPlaybackTime
        current_buffer_size_raw = csvfile.CurrentBufferSize
        current_buffer_size = [0 if i < 0 else i for i in current_buffer_size_raw] #convert negative values to 0

        current_playback_state = csvfile.CurrentPlaybackState
        action = csvfile.Action

        # csvfile= csv.reader(open(bufferlog, 'r'), delimiter=',')
        # epoch_time = list(zip(*csvfile))[0]
        # current_playback_time = list(zip(*csvfile))[1]
        # current_buffer_size = list(zip(*csvfile))[2]
        # current_playback_state = list(zip(*csvfile))[3]
        # action = list(zip(*csvfile))[4]

        indices_buffering = [i for i, x in enumerate(current_playback_state) if x == "BUFFERING"]
        indices_playing = [i for i, x in enumerate(current_playback_state) if x == "PLAY"]
        indices_stopping = [i for i, x in enumerate(current_playback_state) if x == "STOP"]
        indices_writing = [i for i, x in enumerate(action) if x == "Writing"]
        indices_transition = [i for i, x in enumerate(action) if x == "-"]

        isnotbuffering = 1
        iswriting = 0
        isplaying = 0

        buffers = [current_buffer_size[0]]

        for i in range(1, len(epoch_time)):

            if i in indices_buffering and i not in indices_transition:
                isnotbuffering = 0
            if i in indices_writing:
                iswriting = 1
            if ((i in indices_playing or i in indices_stopping) and i not in indices_transition) or i in indices_buffering or i in indices_transition:
                isplaying = 1

            current_buffer_s = isnotbuffering * buffers[i-1] + iswriting * segmentduration - isplaying * (epoch_time[i] - epoch_time[i-1])
            buffers.append(current_buffer_s)

        #CM: interpolating to 1s granularity
        x_interp = range(0,int(epoch_time[len(epoch_time)-1])+1)
        buffers_interp=numpy.interp(x_interp,epoch_time,buffers)

        # buffers_avg=numpy.mean(buffers)
        # buffers_max=max(buffers)
        # buffers_min=min(buffers)
        # buffers_q1=numpy.percentile(buffers, q1)
        # buffers_q2=numpy.percentile(buffers, q2)
        # buffers_q3=numpy.percentile(buffers, q3)
        # buffers_q4=numpy.percentile(buffers, q4)

        buffers_avg=numpy.mean(buffers_interp)
        buffers_max=max(buffers_interp)
        buffers_min=min(buffers_interp)
        buffers_q1=numpy.percentile(buffers_interp, q1)
        buffers_q2=numpy.percentile(buffers_interp, q2)
        buffers_q3=numpy.percentile(buffers_interp, q3)
        buffers_q4=numpy.percentile(buffers_interp, q4)

        #print str(buffers_avg) + ',' + str(buffers_max) + ',' + str(buffers_min) + ',' + str(buffers_q1) + ',' + str(buffers_q2) + ',' + str(buffers_q3) + ',' + str(buffers_q4)
        return str(buffers_avg) + ',' + str(buffers_max) + ',' + str(buffers_min) + ',' + str(buffers_q1) + ',' + str(buffers_q2) + ',' + str(buffers_q3) + ',' + str(buffers_q4)

    except Exception as e:
        print ('[ERROR] AStream calculateBuffer exception: {}').format(e)
        return 'NA,NA,NA,NA,NA,NA,NA'

def calculateStallings(segmentlog,q1,q2,q3,q4):

    try:
        json_in = open(segmentlog)
        clientlog=json.load(json_in)
        playback_info = clientlog["playback_info"]
        interruptions = playback_info["interruptions"]
        num_stalls = interruptions["count"]
        stalls_total_duration = interruptions["total_duration"]

        down_shifts = playback_info["down_shifts"]
        up_shifts = playback_info["up_shifts"]

        durstalls = []

        if num_stalls > 0:
            events = interruptions["events"]
            for event in events:
                if (event[0] is not None) and (event[1] is not None):
                    durstall_current = event[1] - event[0]
                    durstalls.append(durstall_current)
        else:
            durstalls.append(0)

        durstalls_avg=numpy.mean(durstalls)
        durstalls_max=max(durstalls)
        durstalls_min=min(durstalls)
        durstalls_q1=numpy.percentile(durstalls, q1)
        durstalls_q2=numpy.percentile(durstalls, q2)
        durstalls_q3=numpy.percentile(durstalls, q3)
        durstalls_q4=numpy.percentile(durstalls, q4)

        return str(num_stalls) + ',' + str(durstalls_avg) + ',' + str(durstalls_max) + ',' + str(durstalls_min) + ',' + str(durstalls_q1) + ',' + str(durstalls_q2) + ',' + str(durstalls_q3) + ',' + str(durstalls_q4) + ',' + str(stalls_total_duration) + ',' + str(up_shifts) + ',' + str(down_shifts)

    except Exception as e:
        print ('[ERROR] AStream calculateStallings exception: {}').format(e)
        return "NA,NA,NA,NA,NA,NA,NA,NA,NA,NA,NA"

if __name__ == '__main__':
    """The main thread control the processes (experiment/metadata))."""
    # Try to get the experiment config as provided by the scheduler
    try:
        with open(CONFIGFILE) as configfd:
            EXPCONFIG.update(json.load(configfd))
    except Exception as e:
        print("Cannot retrive expconfig {}".format(e))
        raise e

    if DEBUG:
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

    sequence_number = 0
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

        cmd1=["route","del","default"]
        #os.system(bashcommand)
        try:
                check_output(cmd1)
        except CalledProcessError as e:
                if e.returncode == 28:
                         print("Time limit exceeded for command1")
        #gw_ip="192.168."+str(meta_info["IPAddress"].split(".")[2])+".1"
        gw_ip="undefined"
        for g in netifaces.gateways()[netifaces.AF_INET]:
            if g[1] == ifname:
                gw_ip = g[0]
                break

        cmd2=["route", "add", "default", "gw", gw_ip,str(ifname)]
        try:
                check_output(cmd2)
        except CalledProcessError as e:
                 if e.returncode == 28:
                        print("Time limit exceeded for command2")

        cmd3=["ip", "route", "get", "8.8.8.8"]
        try:
                output=check_output(cmd3)
        except CalledProcessError as e:
                 if e.returncode == 28:
                        print("Time limit exceeded for command3")
        output = output.strip(' \t\r\n\0')
        output_interface=output.split(" ")[4]
        if output_interface==str(ifname):
                print("Source interface is set to " + str(ifname))

        if EXPCONFIG['verbosity'] > 1:
            print("Starting experiment")

        # Create an experiment process and start it
        start_time_exp=time.time()
        exp_process = create_exp_process(meta_info, EXPCONFIG)
        exp_process.start()

        while (time.time() - start_time_exp < exp_grace and
               exp_process.is_alive()):
            # Here we could add code to handle interfaces going up or down
            # Similar to what exist in the ping experiment
            # However, for now we just abort if we loose the interface

            if not check_if(ifname):
                if EXPCONFIG['verbosity'] > 0:
                    print("Interface went down during an experiment")
                break
            elapsed_exp = time.time() - start_time_exp
            if EXPCONFIG['verbosity'] > 1:
                print("Running Experiment for {} s".format(elapsed_exp))
            time.sleep(ifup_interval_check)

        if exp_process.is_alive():
            exp_process.terminate()
        if meta_process.is_alive():
            meta_process.terminate()

        elapsed = time.time() - start_time
        if EXPCONFIG['verbosity'] > 1:
            print("Finished {} after {}".format(ifname, elapsed))
        time.sleep(time_between_experiments)

    if EXPCONFIG['verbosity'] > 1:
        print("Complete experiment took {}, now exiting".format(time.time() - tot_start_time))
