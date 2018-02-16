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
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import json
import zmq
import re
import netifaces
import time
import subprocess
import shlex
import socket
import shutil
import struct
import random
import netifaces as ni
from subprocess import check_output, CalledProcessError
from multiprocessing import Process, Manager

import run_experiment

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
DEBUG = False
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
        "ifup_interval_check": 6,  # Interval to check if interface is up
        "time_between_experiments": 5,
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "modeminterfacename": "InternalInterface",
"urls": [['facebook.com/telia/', 'facebook.com/LeoMessi/', 'facebook.com/Cristiano/', 'facebook.com/intrepidtravel', 'facebook.com/threadless', 'facebook.com/Nutella', 'facebook.com/zappos', 'facebook.com/toughmudder', 'facebook.com/stjude', 'facebook.com/Adobe/'],
              ['en.wikipedia.org/wiki/Timeline_of_the_far_future', 'en.wikipedia.org/wiki/As_Slow_as_Possible', 'en.wikipedia.org/wiki/List_of_political_catchphrases', 'en.wikipedia.org/wiki/1958_Lituya_Bay_megatsunami', 'en.wikipedia.org/wiki/Yonaguni_Monument#Interpretations', 'en.wikipedia.org/wiki/Crypt_of_Civilization', 'en.wikipedia.org/wiki/Mad_scientist', 'en.wikipedia.org/wiki/London_Stone', 'en.wikipedia.org/wiki/Internet', 'en.wikipedia.org/wiki/Stream_Control_Transmission_Protocol'],
        	  ['linkedin.com/company/teliacompany', 'linkedin.com/company/google', 'linkedin.com/company/facebook', 'linkedin.com/company/ericsson', 'linkedin.com/company/microsoft', 'linkedin.com/company/publications-office-of-the-european-union', 'linkedin.com/company/booking.com', 'linkedin.com/company/vodafone', 'linkedin.com/company/bmw', 'linkedin.com/company/t-mobile'],
 		['uk.sports.yahoo.com', 'www.yahoo.com/movies/', 'flickr.com', 'yahoo.com/news/weather/', 'yahoo.jobbdirekt.se', 'uk.news.yahoo.com', 'yahoo.com/style/', 'yahoo.com/beauty', 'se.yahoo.com', 'uk.sports.yahoo.com/football/'],
 	['instagram.com/leomessi/', 'instagram.com/iamzlatanibrahimovic/', 'instagram.com/nike/', 'instagram.com/adidasoriginals/', 'instagram.com/cristiano/', 'instagram.com/natgeo/', 'instagram.com/fcbarcelona/', 'instagram.com/realmadrid/', 'instagram.com/9gag/', 'instagram.com/adele/'],
 		['google.com/search?q=Pok%C3%A9mon+Go', 'google.com/search?q=iPhone+7', 'google.com/search?q=Brexit', 'google.com/#q=stockholm,+sweden', 'google.com/#q=game+of+thrones', 'google.com/#q=Oslo', 'google.com/#q=Paris', 'google.com/#q=Madrid', 'google.com/#q=Rome', 'google.com/#q=the+revenant'],
 		  ['youtube.com/watch?v=544vEgMiMG0', 'youtube.com/watch?v=bcdJgjNDsto', 'youtube.com/watch?v=xGJ5a7uIZ1g', 'youtube.com/watch?v=-Gj4iCZhx7s', 'youtube.com/watch?v=dPTglkp4Lpw', 'youtube.com/watch?v=igEKvkBjMr0', 'youtube.com/watch?v=7-JVmMzGceQ', 'youtube.com/watch?v=ubes1I4Vf4o', 'youtube.com/watch?v=5mmpozjIxKU', 'youtube.com/watch?v=swELkJgTaNQ', 'youtube.com/watch?v=6oX5weDuiVM'],
 		  ['ebay.com/', 'ebay.com/rpp/electronics-en', 'ebay.com/rpp/electronics-en-cameras', 'ebay.com/rpp/sporting-goods-en', 'ebay.com/sch/Cycling-/7294/i.html', 'ebay.com/globaldeals', 'ebay.com/sch/Cell-Phones-Smartphones-/9355/i.html', 'ebay.com/globaldeals/tech/laptops-netbooks', 'ebay.com/rpp/home-and-garden-en', 'ebay.com/sch/Furniture-/3197/i.html'],
 		    ['nytimes.com','nytimes.com/section/science?action=click&pgtype=Homepage&region=TopBar&module=HPMiniNav&contentCollection=Science&WT.nav=page','nytimes.com/section/science/earth?action=click&contentCollection=science&region=navbar&module=collectionsnav&pagetype=sectionfront&pgtype=sectionfront','nytimes.com/section/science/space?action=click&contentCollection=science&region=navbar&module=collectionsnav&pagetype=sectionfront&pgtype=sectionfront', 'nytimes.com/section/health?action=click&contentCollection=science&module=collectionsnav&pagetype=sectionfront&pgtype=sectionfront&region=navbar', 'nytimes.com/section/sports?WT.nav=page&action=click&contentCollection=Sports&module=HPMiniNav&pgtype=Homepage&region=TopBar', 'nytimes.com/section/fashion?WT.nav=page&action=click&contentCollection=Style&module=HPMiniNav&pgtype=Homepage&region=TopBar','nytimes.com/pages/dining/index.html?action=click&pgtype=Homepage&region=TopBar&module=HPMiniNav&contentCollection=Food&WT.nav=page', 'cooking.nytimes.com/recipes/1013616-quinoa-and-chard-cakes?action=click&module=RecirculationRibbon&pgType=recipedetails&rank=3', 'nytimes.com/2017/04/10/upshot/how-many-pills-are-too-many.html?rref=collection%2Fsectioncollection%2Fhealth&action=click&contentCollection=health&region=stream&module=stream_unit&version=latest&contentPlacement=6&pgtype=sectionfront&_r=0'],
 		['theguardian.com/international','theguardian.com/sport/2017/apr/12/new-gender-neutral-cricket-laws-officially-released-by-mcc','theguardian.com/uk/lifeandstyle','theguardian.com/lifeandstyle/2017/apr/11/vision-thing-how-babies-colour-in-the-world','theguardian.com/us-news/2017/apr/12/charging-bull-new-york-fearless-girl-statue-copyright-claim','theguardian.com/business/live/2017/apr/12/brexit-blow-to-workers-as-real-pay-starts-to-fall-again-business-live','theguardian.com/football','theguardian.com/football/2017/apr/11/juventus-barcelona-champions-league-quarter-final-match-report','theguardian.com/football/2017/apr/11/barcelona-neymar-clasico-ban','theguardian.com/uk/technology']],
        "http_protocols":["h1s","h2"],
        "iterations": 1,
        "allowed_interfaces": ["op0",
                               "op1",
                               "op2",
							   "eth0"],  # Interfaces to run the experiment on
        "interfaces_without_metadata": ["eth0"]  # Manual metadata on these IF
        }
def set_source(ifname):
    cmd1=["route",
          "del",
          "default"]
    try:
            check_output(cmd1)
    except CalledProcessError as e:
            if e.returncode == 28:
                print "Time limit exceeded"
                return 0

    gw_ip="undefined"
    for g in ni.gateways()[ni.AF_INET]:
           if g[1] == ifname:
                gw_ip = g[0]
                break

    cmd2=["route", "add", "default", "gw", gw_ip,str(ifname)]
    try:
        check_output(cmd2)
        cmd3=["ip", "route", "get", "8.8.8.8"]
        output=check_output(cmd3)
        output = output.strip(' \t\r\n\0')
        output_interface=output.split(" ")[4]
        if output_interface==str(ifname):
                print "Source interface is set to "+str(ifname)
        else:
                print "Source interface "+output_interface+"is different from "+str(ifname)
                return 0

    except CalledProcessError as e:
        if e.returncode == 28:
            print "Time limit exceeded"
            return 0
    return 1

def check_dns():
    cmd=["dig",
         "www.google.com",
         "+noquestion", "+nocomments", "+noanswer"]
    ops_dns_used=0
    try:
           out=check_output(cmd)
           data=dns_list.replace("\n"," ")
           for line in out.splitlines():
                  for ip in re.findall(r'(?:\d{1,3}\.)+(?:\d{1,3})',data):
                        if ip in line:
                            ops_dns_used=1
                            print line
    except CalledProcessError as e:
           if e.returncode == 28:
                print "Time limit exceeded"
                if ops_dns_used==1:
                    print "Operators dns is set properly"

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
    print str
    return str



def py_traceroute(dest_name):
    dest_addr = socket.gethostbyname(dest_name)
    port = 33434
    max_hops = 30
    icmp = socket.getprotobyname('icmp')
    udp = socket.getprotobyname('udp')
    ttl = 1

    tr_output=""
    while True:
        recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, udp)
        send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
        
        # Build the GNU timeval struct (seconds, microseconds)
        timeout = struct.pack("ll", 5, 0)
        
        # Set the receive timeout so we behave more like regular traceroute
        recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeout)
        
        recv_socket.bind(("", port))
        #sys.stdout.write(" %d  " % ttl)
        send_socket.sendto("", (dest_name, port))
        curr_addr = None
        curr_name = None
        finished = False
        tries = 3
        while not finished and tries > 0:
            try:
                _, curr_addr = recv_socket.recvfrom(512)
                finished = True
                curr_addr = curr_addr[0]
                try:
                    curr_name = socket.gethostbyaddr(curr_addr)[0]
                except socket.error:
                    curr_name = curr_addr
            except socket.error as (errno, errmsg):
                tries = tries - 1
                sys.stdout.write("* ")
        
        send_socket.close()
        recv_socket.close()
        
        if not finished:
            pass
        
        if curr_addr is not None:
            curr_host = "%s (%s)" % (curr_name, curr_addr)
        else:
            curr_host = ""
            curr_addr = " "
        tr_output+=curr_addr+" "

        ttl += 1
        if curr_addr == dest_addr or ttl > max_hops:
            break
    return tr_output


def run_exp(meta_info, expconfig, url,count,no_cache):
    """Seperate process that runs the experiment and collect the ouput.

        Will abort if the interface goes down.
    """
    ifname = meta_info[expconfig["modeminterfacename"]]

    #url=url_list[index]
    print "Deleting old profiles from the temp dir.."

    root="/tmp/"
    try:
        for item in os.listdir(root):
            if os.path.isdir(os.path.join(root, item)):
                print "/tmp/"+item
                if "tmp" in item or "rust" in item:
                    print item
                    shutil.rmtree("/tmp/"+item)
    except OSError, e:  ## if failed, report it back to the user ##
        print ("Error: %s - %s." % (e.filename,e.strerror))

    #print "Starting tracerouting ..."

    #try:
    #	routes=py_traceroute(str(url).split("/")[0])
    #except Exception:
    #	print ("tracerouting unsuccessful")
    #
    print "Starting ping ..."

    try:
    	response = subprocess.check_output(
        ['fping', '-I',ifname,'-c', '3', '-q', str(url).split("/")[0]],
        stderr=subprocess.STDOUT,  # get all output
        universal_newlines=True  # return string not bytes
    	)
    	ping_outputs= response.splitlines()[-1].split("=")[-1]
    	ping_output=ping_outputs.split("/")
        ping_min = ping_output[0]
    	ping_avg = ping_output[1]
    	ping_max = ping_output[2]
    except subprocess.CalledProcessError:
    	response = None
	print "Ping info is unknown"

    har_stats={}
    har_stats=run_experiment.browse_firefox(har_directory,domains,getter,count,no_cache,url,getter_version)
    
#    try:
#        har_stats["route"]=routes
#    except Exception:
#       print "traceroute info is not available"
#
    try:
    	har_stats["ping_max"]=ping_max
        har_stats["ping_avg"]=ping_avg
	har_stats["ping_min"]=ping_min
	har_stats["ping_exp"]=1
    except Exception:
	print("Ping info is not available")
        har_stats["ping_exp"]=0

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
    	har_stats["InternalInterface"]=meta_info["InternalInterface"]
    except Exception:
    	print("InternalInterface info is not available")
    try:
    	har_stats["IPAddress"]=meta_info["IPAddress"]
    except Exception:
    	print("IPAddress info is not available")
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
#
    har_stats["SequenceNumber"]= count

    #msg=json.dumps(har_stats)

    filename=har_stats["filename"]
    har_stats.pop("filename")
    with open('/tmp/'+str(har_stats["NodeId"])+'_'+str(har_stats["DataId"])+'_'+str(har_stats["Timestamp"])+'.json', 'w') as outfile:
        json.dump(har_stats, outfile)
    
    if expconfig['verbosity'] > 2:
            #print har_stats
            print("Done with  Node: {}, HTTP protocol: {}, url: {}, Operator: {}".format(har_stats["NodeId"], har_stats["Protocol"],har_stats["url"],har_stats["Operator"]))
    if not DEBUG:
	    #print har_stats
            print("Done with  Node: {}, HTTP protocol: {}, url: {}, Operator: {}".format(har_stats["NodeId"], har_stats["Protocol"],har_stats["url"],har_stats["Operator"]))
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


def create_meta_process(ifname, expconfig):
    meta_info = Manager().dict()
    process = Process(target=metadata,
                      args=(meta_info, ifname, expconfig, ))
    process.daemon = True
    return (meta_info, process)


def create_exp_process(meta_info, expconfig,url,count,no_cache):
    process = Process(target=run_exp, args=(meta_info, expconfig,url,count,no_cache))
    process.daemon = True
    return process


if __name__ == '__main__':
    """The main thread control the processes (experiment/metadata))."""
    # Settings related to browsing 

    os.system('clear')
    current_directory = os.path.dirname(os.path.abspath(__file__))
    har_directory  = os.path.join(current_directory, "har")
        
    print 'Checking if HTTP Archive directory exists . . . . . . . .'
    if os.path.exists(har_directory):
        print 'HTTP Archive Directory Exists!'
    else:
        os.mkdir(har_directory)
        print "HTTP Archive Directory created successfully in %s .." % (har_directory)



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
	iterations=EXPCONFIG['iterations']
        urls=EXPCONFIG['urls']
	http_protocols=EXPCONFIG['http_protocols']
        if_without_metadata = EXPCONFIG['interfaces_without_metadata']
        meta_grace = EXPCONFIG['meta_grace']
        #exp_grace = EXPCONFIG['exp_grace'] + EXPCONFIG['time']
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
        print "Missing expconfig variable {}".format(e)
        raise e

    start_time = time.time()
    
    if type(urls) is list:
        random.shuffle(urls)
    else:
        urls_name=urls
        urls=[]
        urls.append(urls_name)    
    
    for url_list in urls:
        if type(url_list) is list:
        	print "Randomizing the url lists .."
                random.shuffle(url_list)    
        else:
                url_name=url_list
                url_list=[]
		url_list.append(url_name)

        try:
		for ifname in allowed_interfaces:
	       		if ifname not in open('/proc/net/dev').read():
		      		allowed_interfaces.remove(ifname)
    	except Exception as e:
        	print "Cannot remove nonexisting interface {}".format(e)
        	raise e
		continue
	

        no_cache=1
        for ifname in allowed_interfaces:
	    first_run=1 
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
                add_manual_metadata_information(meta_info, ifname,EXPCONFIG)
    #
            # Try to get metadadata
            # if the metadata process dies we retry until the IF_META_GRACE is up
            start_time_metacheck = time.time()
            while (time.time() - start_time_metacheck < meta_grace and
                   not check_meta(meta_info, meta_grace, EXPCONFIG)):
                if not meta_process.is_alive():
                    # This is serious as we will not receive updates
                    # The meta_info dict may have been corrupt so recreate that one
                    meta_info, meta_process = create_meta_process(ifname,
                                                                  EXPCONFIG)
                    meta_process.start()
                if EXPCONFIG['verbosity'] > 1:
                    print "Trying to get metadata. Waited {:0.1f}/{} seconds.".format(time.time() - start_time_metacheck, meta_grace)
                time.sleep(ifup_interval_check) 

            # Ok we did not get any information within the grace period
            # we give up on that interface
            if not check_meta(meta_info, meta_grace, EXPCONFIG):
                if EXPCONFIG['verbosity'] > 1:
                    print "No Metadata continuing"
                continue    

            # Ok we have some information lets start the experiment script


	    #output_interface=None

	    if not DEBUG:
		
	    	# set the source route
		if not set_source(ifname):
			continue		
			
		print "Creating operator specific dns.."
		dns_list=""
		dns_list=add_dns(str(ifname))
			
		print "Checking the dns setting..."
		check_dns()	
		  

	    

            if EXPCONFIG['verbosity'] > 1:
                print "Starting experiment"
        
	    for url in url_list:	
            	if first_run ==1:
	    		no_cache=1
			first_run=0
	    	else:
			no_cache=0
		if type(http_protocols) is list: 
	        	random.shuffle(http_protocols)
		else:
			protocol=http_protocols
			http_protocols=[]
			http_protocols.append(protocol)

    	    	for protocol in http_protocols:
    			if protocol == 'h1':
                			getter = h1
                			getter_version = 'HTTP1.1'
            		elif protocol == 'h1s':
                			getter = h1s
                			getter_version = 'HTTP1.1/TLS'
            		elif protocol == 'h2':
                			getter = h2
                			getter_version = 'HTTP2'
            		else:
                			print 'Unknown HTTP Scheme: <HttpMethod:h1/h1s/h2>' 
                			sys.exit()	
                	for run in range(start_count, iterations):
                    		# Create a experiment process and start it
                    		start_time_exp = time.time()
                    		exp_process = exp_process = create_exp_process(meta_info, EXPCONFIG, url,run+1, no_cache)
                    		exp_process.start()
            
                    		while (time.time() - start_time_exp < exp_grace and
                           			exp_process.is_alive()):
                        			# Here we could add code to handle interfaces going up or down
                        			# Similar to what exist in the ping experiment
                        			# However, for now we just abort if we loose the interface
            
                        		# No modem information hack to add required information
                        		if (check_if(ifname) and ifname in if_without_metadata):
                        		    add_manual_metadata_information(meta_info, ifname, EXPCONFIG)    

                                            if not meta_process.is_alive():
                                                print "meta_process is not alive - restarting"
                                                meta_info, meta_process = create_meta_process(ifname, EXPCONFIG)
                                                meta_process.start()
                                                time.sleep(3*ifup_interval_check)   

            
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
                    		#if meta_process.is_alive():
                        	#		meta_process.terminate()
            
                    		elapsed = time.time() - start_time
                    		if EXPCONFIG['verbosity'] > 1:
                        			print "Finished {} after {}".format(ifname, elapsed)
                    		time.sleep(time_between_experiments)  
	    if meta_process.is_alive():
		meta_process.terminate()
            if EXPCONFIG['verbosity'] > 1:
                print ("Interfaces {} "
                   "done, exiting").format(ifname)
