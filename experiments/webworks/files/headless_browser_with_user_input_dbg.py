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
import netifaces
import time
import subprocess
import socket
import struct
import random
import netifaces as ni
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
        "ifup_interval_check": 6,  # Interval to check if interface is up
        "time_between_experiments": 5,
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "modeminterfacename": "InternalInterface",
        "urls": [['facebook.com/telia/']],
                 #['en.wikipedia.org/wiki/As_Slow_as_Possible'],
                 #['linkedin.com/company/google'],
                 #['instagram.com/nike/'],
                 #['google.com/search?q=iPhone+7'],
                 #['youtube.com/watch?v=xGJ5a7uIZ1g'],
                 #['ebay.com/sch/Cell-Phones-Smartphones-/9355/i.html'],
                 #['nytimes.com/section/science/earth?action=click&contentCollection=science&region=navbar&module=collectionsnav&pagetype=sectionfront&pgtype=sectionfront'],
                 #['theguardian.com/football/2017/apr/11/juventus-barcelona-champions-league-quarter-final-match-report','theguardian.com/football/2017/apr/11/barcelona-neymar-clasico-ban'],
                 #['soupsoup.tumblr.com']],
        "http_protocols":["h1s","h2"],
        "iterations": 1,
        "allowed_interfaces": ["op0","op1","op2","eth0"],  # Interfaces to run the experiment on
        "interfaces_without_metadata": ["eth0"]  # Manual metadata on these IF
        }

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

    print "Starting ping ..."

    #try:
    #	routes=py_traceroute(str(url).split("/")[0])
    #except Exception:
    #	print ("tracerouting unsuccessful")

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


    print "Starting the display ..."
    #count=run+1
    st=time.time()
    display = Display(visible=0, size=(800, 600))
    display.start()
    print "Display started in {} seconds.".format(time.time()-st)

    d = DesiredCapabilities.FIREFOX
    #d['loggingPrefs'] = {'browser': 'ALL', 'client': 'ALL', 'driver': 'ALL', 'performance': 'ALL', 'server': 'ALL'}
    
    d['marionette'] = True
    d['binary'] = '/usr/bin/firefox'
    print "Creating Firefox profile .."
    try:
    	profile = webdriver.FirefoxProfile("/opt/monroe/")
    except Exception as e:
	raise WebDriverException("Unable to set FF profile in  webdriver.", e)
        return

    print "Setting different Firefox profile .."
    #set firefox preferences

    profile.accept_untrusted_certs = True
    profile.add_extension("har.xpi")
    
    #set firefox preferences
    if no_cache==1:
    	profile.set_preference('browser.cache.memory.enable', False)
    	profile.set_preference('browser.cache.offline.enable', False)
    	profile.set_preference('browser.cache.disk.enable', False)
    	profile.set_preference('network.http.use-cache', False)
    else:
    	profile.set_preference('browser.cache.memory.enable', True)
    	profile.set_preference('browser.cache.offline.enable', True)
    	profile.set_preference('browser.cache.disk.enable', True)
    	profile.set_preference('network.http.use-cache', True)

    profile.set_preference("app.update.enabled", False)
   # profile.set_preference('browser.cache.memory.enable', False)
   # profile.set_preference('browser.cache.offline.enable', False)
   # profile.set_preference('browser.cache.disk.enable', False)
    profile.set_preference('browser.startup.page', 0)
    profile.set_preference("general.useragent.override", "Mozilla/5.0 (Android 4.4; Mobile; rv:46.0) Gecko/46.0 Firefox/46.0")
    
    #Check the HTTP(getter) scheme and disable the rest
    if getter_version == 'HTTP1.1':
        profile.set_preference('network.http.spdy.enabled.http2', False)
        profile.set_preference('network.http.spdy.enabled', False)
        profile.set_preference('network.http.spdy.enabled.v3-1', False)
        profile.set_preference('network.http.max-connections-per-server', 6)
        filename = "h1-"+url.split("/")[0]+"."+str(count)
    elif getter_version == 'HTTP1.1/TLS':
        profile.set_preference('network.http.spdy.enabled.http2', False)
        profile.set_preference('network.http.spdy.enabled', False)
        profile.set_preference('network.http.spdy.enabled.v3-1', False)
        profile.set_preference('network.http.max-connections-per-server', 6)
        filename = "h1s-"+url.split("/")[0]+"."+str(count)
    elif getter_version == 'HTTP2':
        profile.set_preference('network.http.spdy.enabled.http2', True)
        profile.set_preference('network.http.spdy.enabled', True)
        profile.set_preference('network.http.spdy.enabled.v3-1', True )
        filename = "h2-"+url.split("/")[0]+"."+str(count)
    
    
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
    profile.set_preference('webdriver.load.strategy', 'unstable')
    time.sleep(1)

    print "Profile for the Firefox is set"

    #create firefox driver

    print "Creating the Firefox driver .."

    try:
        st=time.time()
        driver = webdriver.Firefox(capabilities=d,firefox_profile=profile)
        print "Driver started in {} seconds.".format(time.time()-st)

	driver.set_page_load_timeout(100)
        #driver.manage.timeouts().pageLoadTimeout(100,SECONDS)
        #driver.manage.timeouts().setScriptTimeout(100,SECONDS)
        st=time.time()
        driver.get(newurl)
        print "Driver.get returned in {} seconds.".format(time.time()-st)
	
	navigationStart = driver.execute_script("return window.performance.timing.navigationStart")
	responseStart = driver.execute_script("return window.performance.timing.responseStart")
	domComplete = driver.execute_script("return window.performance.timing.domComplete")
        loadeventStart= driver.execute_script("return window.performance.timing.loadEventStart")

	backendPerformance = responseStart - navigationStart
	frontendPerformance = domComplete - responseStart
	plt = loadeventStart - navigationStart

	print "Back End: %s" % backendPerformance
	print "Front End: %s" % frontendPerformance
	print "Page load time: %s" % plt
	#timestr = time.strftime("%Y%m%d-%H%M%S")
	#driver.save_screenshot(timestr+".png")
    except Exception as e:
        raise WebDriverException("Unable to start webdriver with FF.", e)
        return
    
    time.sleep(5)
    print "Quiting the driver.."
    #driver.save_screenshot('screenie.png')

    #close the firefox driver after HAR is written
    driver.close()

    print "Terminating the display .."

    display.popen.terminate()

    display.stop()
    print "Killing geckodriver explicitely .."
    try:
        output=check_output("kill $(ps aux | pgrep -fla geckodriver| awk '{print $1}')",shell=True)
    except CalledProcessError as e:
        if e.returncode == 28:
                print "Time limit exceeded"

    har_stats={}
    objs=[]
    pageSize=0

    print "Processing the HAR files ..."

    try:
    	with open("har/"+filename+".har") as f:
        	msg=json.load(f)
    		num_of_objects=0

    		start=0
    		for entry in msg["log"]["entries"]:
        		try:
                		obj={}
                		obj["url"]=entry["request"]["url"]
               			obj["objectSize"]=entry["response"]["bodySize"]+entry["response"]["headersSize"]
                		pageSize=pageSize+entry["response"]["bodySize"]+entry["response"]["headersSize"]
				obj["mimeType"]=entry["response"]["content"]["mimeType"]
				obj["startedDateTime"]=entry["startedDateTime"]
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
                
    		har_stats["Objects"]=objs
    		har_stats["NumObjects"]=num_of_objects
    		har_stats["PageSize"]=pageSize
    except IOError:
    	print "har/"+filename+".har doesn't exist"
        

    #try:
    #   har_stats["tracedRoutes"]=routes.rstrip().split(" ")
    #except Exception:
    #   print "traceroute info is not available"

    try:
    	har_stats["ping_max"]=ping_max
        har_stats["ping_avg"]=ping_avg
	har_stats["ping_min"]=ping_min
	har_stats["ping_exp"]=1
    except Exception:
	print("Ping info is not available")
        har_stats["ping_exp"]=0
    try:
    	hours,minutes,seconds=str(((parse(end_time)+ datetime.timedelta(milliseconds=ms))- parse(start_time))).split(":")
    	hours = int(hours)
    	minutes = int(minutes)
    	seconds = float(seconds)
    	plt_ms = int(3600000 * hours + 60000 * minutes + 1000 * seconds)
    	har_stats["Web load time2"]=plt_ms
    except:
    	print "Timing errors in web load time"

    har_stats["url"]=url
    har_stats["Protocol"]=getter_version	
    har_stats["Web load time1"]=plt
    har_stats["ttfb"]=backendPerformance
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
    #try:
    #	har_stats["IMSI"]=meta_info["IMSI"]
    #except Exception:
    #	print("IMSI info is not available")
    #try:
    #	har_stats["IMEI"]=meta_info["IMEI"]
    #except Exception:
    #	print("IMEI info is not available")
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
#
    har_stats["SequenceNumber"]= count

    #msg=json.dumps(har_stats)
    with open('/tmp/'+str(har_stats["NodeId"])+'_'+str(har_stats["DataId"])+'_'+str(har_stats["Timestamp"])+'.json', 'w') as outfile:
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
    info["ipaddress"] ="172.17.0.2"	


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
        print "HTTP Archive Directory created successfully in %s ..\n" % (har_directory)



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
    for url_list in urls:
	print "Randomizing the url lists .."

        random.shuffle(url_list)    

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

            #cmd1=["route",
            #     "del",
            #     "default"]
            #os.system(bashcommand)
           # try:
            #        check_output(cmd1)
            #except CalledProcessError as e:
             #       if e.returncode == 28:
              #              print "Time limit exceeded"
            
           # gw_ip="undefined"
           # for g in ni.gateways()[ni.AF_INET]:
           #     if g[1] == ifname:
            #        gw_ip = g[0]
             #       break   

           # cmd2=["route", "add", "default", "gw", gw_ip,str(ifname)]
           # try:
            #    check_output(cmd2)
            #	cmd3=["ip", "route", "get", "8.8.8.8"]
             #   output=check_output(cmd3)
            #	output = output.strip(' \t\r\n\0')
            #	output_interface=output.split(" ")[4]
            #	if output_interface==str(ifname):
             #       	print "Source interface is set to "+str(ifname)
    	#	else:
         #           	print "Source interface "+output_interface+"is different from "+str(ifname)
    	#		continue
            
    	 #   except CalledProcessError as e:
          #           if e.returncode == 28:
           #                 print "Time limit exceeded"
    	#	     continue
    	   

            if EXPCONFIG['verbosity'] > 1:
                print "Starting experiment"
        
	    for url in url_list:	
            	if first_run ==1:
	    		no_cache=1
			first_run=0
	    	else:
			no_cache=0
	        random.shuffle(http_protocols)
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
