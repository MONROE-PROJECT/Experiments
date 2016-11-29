#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Mohammad Rajiullah (Used general experiment logic from 
# Jonas Karlsson)
# Date: October 2016
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""
headless firefox browsing using selenium web driver.
The browsing can make request using h1, h2 or h1 over tls.
The script will execute one experiment for each of the allowed_interfaces.
All default values are configurable from the scheduler.
The output will be formated into a json object suitable for storage in the
MONROE db.
"""

import sys, getopt
import time, os
import fileinput
from pyvirtualdisplay import Display
from selenium import webdriver
import datetime
from dateutil.parser import parse
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

from scapy.all import IP, ICMP, sr1

import json
import subprocess
import zmq
import netifaces
import time
from subprocess import check_output, CalledProcessError
from multiprocessing import Process, Manager

urlfile =''
iterations =0 
url=''
num_urls=0
domains = "devtools.netmonitor.har."
num_urls =0
url_list = []
start_count = 0
getter=''
newurl=''
getter_version=''
h1='http://'
h1s='https://'
h2='https://'
current_directory =''
har_directory =''

# Configuration
DEBUG = True
CONFIGFILE = '/monroe/config'

# Default values (overwritable from the scheduler)
# Can only be updated from the main thread and ONLY before any
# other processes are started
EXPCONFIG = {
        "guid": "no.guid.in.config.file",  # Should be overridden by scheduler
        "url": "http://193.10.227.25/test/1000M.zip",
        "size": 3*1024,  # The maximum size in Kbytes to download
        "time": 3600,  # The maximum time in seconds for a download
        "zmqport": "tcp://172.17.0.1:5556",
        "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
        "dataversion": 1,
        "dataid": "MONROE.EXP.FIREFOX.HEADLESS.BROWSING",
        "nodeid": "fake.nodeid",
        "meta_grace": 120,  # Grace period to wait for interface metadata
        "exp_grace": 120,  # Grace period before killing experiment
        "ifup_interval_check": 5,  # Interval to check if interface is up
        "time_between_experiments": 30,
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "modeminterfacename": "InternalInterface",
        "allowed_interfaces": ["op0",
                               "op1",
                               "op2"],  # Interfaces to run the experiment on
        "interfaces_without_metadata": []  # Manual metadata on these IF
        }


def run_exp(meta_info, expconfig, url,count):
    """Seperate process that runs the experiment and collect the ouput.

        Will abort if the interface goes down.
    """
    ifname = meta_info[expconfig["modeminterfacename"]]

    url=url_list[index]

    try:
    	response = subprocess.check_output(
        ['fping', '-I',ifname,'-c', '3', '-nq', url],
        stderr=subprocess.STDOUT,  # get all output
        universal_newlines=True  # return string not bytes
    	)
    	ping_outputs= response.splitlines()[-1].split("=")[-1]
    	ping_output=ping_outputs.split("/")
        ping_mean = ping_output[0]
    	ping_avg = ping_output[1]
    	ping_max = ping_output[2]
    except subprocess.CalledProcessError:
    	response = None
        print "Ping info is unknown"

 
    tr_output=""
    host_or_ip=url
    ip = IP(dst=host_or_ip)

    icmp = ICMP()

    ip.ttl = 1

    while True:

    	res = sr1(ip/icmp, verbose=False)

    	tr_output+=res['IP'].src+" "

    	if res['ICMP'].type == 0:
      		break

    	ip.ttl += 1
    display = Display(visible=0, size=(800, 600))
    display.start()
    profile = webdriver.FirefoxProfile()
    profile.accept_untrusted_certs = True
    profile.add_extension("har.xpi")
    
    #set firefox preferences
    profile.set_preference("app.update.enabled", False)
    profile.set_preference('browser.cache.memory.enable', False)
    profile.set_preference('browser.cache.offline.enable', False)
    profile.set_preference('browser.cache.disk.enable', False)
    profile.set_preference('browser.startup.page', 0)
    
    #Check the HTTP(getter) scheme and disable the rest
    if getter_version == 'HTTP1.1':
        profile.set_preference('network.http.spdy.enabled.http2', False)
        profile.set_preference('network.http.spdy.enabled', False)
        profile.set_preference('network.http.spdy.enabled.v3-1', False)
        profile.set_preference('network.http.max-connections-per-server', 6)
        filename = "h1-"+url[:-1]+"."+str(count)
    elif getter_version == 'HTTP1.1/TLS':
        profile.set_preference('network.http.spdy.enabled.http2', False)
        profile.set_preference('network.http.spdy.enabled', False)
        profile.set_preference('network.http.spdy.enabled.v3-1', False)
        profile.set_preference('network.http.max-connections-per-server', 6)
        filename = "h1s-"+url[:-1]+"."+str(count)
    elif getter_version == 'HTTP2':
        profile.set_preference('network.http.spdy.enabled.http2', True)
        profile.set_preference('network.http.spdy.enabled', True)
        profile.set_preference('network.http.spdy.enabled.v3-1', True )
        filename = "h2-"+url[:-1]+"."+str(count)
    
    
    profile.set_preference('network.prefetch-next', False)
    profile.set_preference('network.http.spdy.enabled.v3-1', False)
    
    newurl = getter+url
    
    #set the preference for the trigger
    profile.set_preference("extensions.netmonitor.har.contentAPIToken", "test")
    profile.set_preference("extensions.netmonitor.har.autoConnect", True)
    profile.set_preference(domains + "defaultFileName", filename)
    profile.set_preference(domains + "enableAutoExportToFile", True)
    profile.set_preference(domains + "defaultLogDir", har_directory)
    profile.set_preference(domains + "pageLoadedTimeout", 1000)
    time.sleep(1)

    #create firefox driver

    try:
        driver = webdriver.Firefox(profile)
        driver.get(newurl)
    except Exception as e:
        raise WebDriverException("Unable to start webdriver with FF.", e)
        return
    
    time.sleep(5)
    #close the firefox driver after HAR is written
    driver.close()
    display.stop()
    har_stats={}
    objs=[]
    pageSize=0

    try:
    	with open("har/"+filename+".har") as f:
        	msg=json.load(f)
    except IOError:
    	print "har/"+filename+".har doesn't exist"
        return
    num_of_objects=0

    start=0
    for entry in msg["log"]["entries"]:
        try:
                obj={}
                obj["url"]=entry["request"]["url"]
                obj["ObjectSize"]=entry["response"]["bodySize"]+entry["response"]["headersSize"]
                pageSize=pageSize+entry["response"]["bodySize"]+entry["response"]["headersSize"]
                obj["time"]=entry["time"]
                obj["timings"]=entry["timings"]
                objs.append(obj)
                num_of_objects=num_of_objects+1
                if start==0:
                        start_time=entry["startedDateTime"]
                        start=1
                end_time=entry["startedDateTime"]
                ms=entry["time"]
    	except KeyError:
        	pass
    try:
    	har_stats["ping_max"]=ping_max
        har_stats["ping_avg"]=ping_avg
	har_stats["ping_min"]=ping_min
	har_stats["ping_exp"]=1
    except Exception:
	print("Ping info is not available")
	har_stats["ping_exp"]=0

    har_stats["trace_rt_ips"]=tr_output
    har_stats["Objects"]=objs
    har_stats["NumObjects"]=num_of_objects
    har_stats["PageSize"]=pageSize
    hours,minutes,seconds=str(((parse(end_time)+ datetime.timedelta(milliseconds=ms))- parse(start_time))).split(":")
    hours = int(hours)
    minutes = int(minutes)
    seconds = float(seconds)
    plt_ms = int(3600000 * hours + 60000 * minutes + 1000 * seconds)
    har_stats["url"]=url[:-1]
    har_stats["Protocol"]=getter_version	
    har_stats["Web load time"]=plt_ms
    har_stats["Guid"]= expconfig['guid']
    har_stats["DataId"]= expconfig['dataid']
    har_stats["DataVersion"]= expconfig['dataversion']
    har_stats["NodeId"]= expconfig['nodeid']
    har_stats["Timestamp"]= time.time()
    try:
    	har_stats["Iccid"]= meta_info["ICCID"]
    except Exception:
    	print("ICCID info is not available")
    try:
    	har_stats["Operator"]= meta_info["Operator"]
    except Exception:
    	print("Operator info is not available")
    try:
    	har_stats["IMSI"]=meta_info["IMSI"]
    except Exception:
    	print("IMSI info is not available")
    try:
    	har_stats["IMEI"]=meta_info["IMEI"]
    except Exception:
    	print("IMEI info is not available")
    try:
    	har_stats["InternalInterface"]=meta_info["InternalInterface"]
    except Exception:
    	print("InternalInterface info is not available")
    try:
    	har_stats["IPAddress"]=meta_info["IPAddress"]
    except Exception:
    	print("IPAddress info is not available")
    try:
    	har_stats["InternalIPAddress"]=meta_info["InternalIPAddress"]
    except Exception:
    	print("InternalIPAddress info is not available")
    try:
    	har_stats["InterfaceName"]=meta_info["InterfaceName"]
    except Exception:
    	print("InterfaceName info is not available")
    try:
    	har_stats["IMSIMCCMNC"]=meta_info["IMSIMCCMNC"]
    except Exception:
    	print("IMSIMCCMNC info is not available")
    try:
    	har_stats["NWMCCMNC"]=meta_info["NWMCCMNC"]
    except Exception:
    	print("NWMCCMNC info is not available")
    try:
    	har_stats["LAC"]=meta_info["LAC"]
    except Exception:
    	print("LAC info is not available")
    try:
    	har_stats["CID"]=meta_info["CID"]
    except Exception:
    	print("CID info is not available")
    try:
    	har_stats["RSCP"]=meta_info["RSCP"]
    except Exception:
    	print("RSCP info is not available")
    try:
    	har_stats["RSSI"]=meta_info["RSSI"]
    except Exception:
    	print("RSSI info is not available")
    try:
    	har_stats["RSRQ"]=meta_info["RSRQ"]
    except Exception:
    	print("RSRQ info is not available")
    try:
    	har_stats["RSRP"]=meta_info["RSRP"]
    except Exception:
    	print("RSRP info is not available")
    try:
    	har_stats["ECIO"]=meta_info["ECIO"]
    except Exception:
    	print("ECIO info is not available")
    try:
    	har_stats["DeviceMode"]=meta_info["DeviceMode"]
    except Exception:
    	print("DeviceMode info is not available")
    try:
    	har_stats["DeviceSubmode"]=meta_info["DeviceSubmode"]
    except Exception:
    	print("DeviceSubmode info is not available")
    try:
    	har_stats["DeviceState"]=meta_info["DeviceState"]
    except Exception:
    	print("DeviceState info is not available")

    har_stats["SequenceNumber"]= count

    #msg=json.dumps(har_stats)
    with open('/tmp/'+filename+'_'+ifname+'.json', 'w') as outfile:
        json.dump(har_stats, outfile)
    
    if expconfig['verbosity'] > 2:
            print har_stats
    if not DEBUG:
	    print har_stats
            monroe_exporter.save_output(har_stats, expconfig['resultdir'])
    try:
        os.remove("/opt/monroe/har/"+filename+".har")
    except OSError, e:  ## if failed, report it back to the user ##
        print ("Error: %s - %s." % (e.filename,e.strerror))
    
    

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
    info["Timestamp"] = time.time()
    info["internalIPAddress"]="172.17.0.2"


def create_meta_process(ifname, expconfig):
    meta_info = Manager().dict()
    process = Process(target=metadata,
                      args=(meta_info, ifname, expconfig, ))
    process.daemon = True
    return (meta_info, process)


def create_exp_process(meta_info, expconfig,url,count):
    process = Process(target=run_exp, args=(meta_info, expconfig,url,count))
    process.daemon = True
    return process


if __name__ == '__main__':
    """The main thread control the processes (experiment/metadata))."""
    # Settings related to browsing 


    if len(sys.argv) ==  1: 
        print 'Use: headless_browser.py  <URL_File>  <Iterations> <HttpMethod:h1/h1s/h2>'
        sys.exit()
    elif len(sys.argv) ==  2:
        print 'Use: headless_browser.py  <URL_File>  <Iterations> <HttpMethod:h1/h1s/h2>'
        sys.exit()
    elif len(sys.argv) ==  3:
        print 'Use: headless_browser.py  <URL_File>  <Iterations> <HttpMethod:h1/h1s/h2>'
        sys.exit()
    elif len(sys.argv) ==  4:
        urlfile = sys.argv[1]
        iterations = int(sys.argv[2])

        if sys.argv[3] == 'h1':
            getter = h1
            getter_version = 'HTTP1.1'
        elif sys.argv[3] == 'h1s':
            getter = h1s
            getter_version = 'HTTP1.1/TLS'
        elif sys.argv[3] == 'h2':
            getter = h2
            getter_version = 'HTTP2'
        else:
            print 'Unknown HTTP Scheme: <HttpMethod:h1/h1s/h2>'
            print 'Use: headless_browser.py  <URL_File>  <Iterations> <HttpMethod:h1/h1s/h2>'  
            sys.exit()
        
        os.system('clear')
        current_directory = os.path.dirname(os.path.abspath(__file__))
        har_directory  = os.path.join(current_directory, "har")
        
        print 'Checking if HTTP Archive directory exists . . . . . . . .'
        if os.path.exists(har_directory):
            print 'HTTP Archive Directory Exists!'
        else:
            os.mkdir(har_directory)
            print "HTTP Archive Directory created successfully in %s ..\n" % (har_directory)

        print "Current Directory is: %s" % (current_directory)
        print "HTTP Archive Directory is: %s" % (har_directory)
        print 'URL file is: ', urlfile
        print 'Number of Iterations: ', iterations
        print "HTTP Scheme is: %s" % (getter_version)
        print '----------------------------------\n'
        print 'List of URLs to fetch are: \n'
        
        loop = iterations
        
        with open(sys.argv[1], "r") as ins:
            for line in ins:
                #Make URL with passed in HTTP getter scheme
                #newurl = getter + line
                #Add each URL to the url_list
                url_list.append(line)
                #Print URLs
                print getter+url_list[num_urls-1]


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
      #  if (check_if(ifname) and ifname in if_without_metadata):
       #     add_manual_metadata_information(meta_info, ifname, EXPCONFIG)
#
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


	output_interface=None

#        cmd1=["route",
#             "del",
#             "default"]
#        #os.system(bashcommand)
#        try:
#                check_output(cmd1)
#        except CalledProcessError as e:
#                if e.returncode == 28:
#                        print "Time limit exceeded"
#        gw_ip="192.168."+str(meta_info["InternalIPAddress"].split(".")[2])+".1"
#        cmd2=["route", "add", "default", "gw", gw_ip,str(ifname)]
#        try:
#                check_output(cmd2)
#        	cmd3=["ip", "route", "get", "8.8.8.8"]
#                output=check_output(cmd3)
#        	output = output.strip(' \t\r\n\0')
#        	output_interface=output.split(" ")[4]
#        	if output_interface==str(ifname):
#                	print "Source interface is set to "+str(ifname)
#		else:
#			continue
#        
#	except CalledProcessError as e:
#                 if e.returncode == 28:
#                        print "Time limit exceeded"
#		 continue
#	
#
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
                    #if (check_if(ifname) and ifname in if_without_metadata):
                    #    add_manual_metadata_information(meta_info, ifname, EXPCONFIG)
        
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
