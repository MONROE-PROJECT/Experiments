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


def browse_firefox(har_directory,domains,getter,count,no_cache,url,getter_version):
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
    
    
    #profile.set_preference('network.prefetch-next', False)
    #profile.set_preference('network.http.spdy.enabled.v3-1', False)
    
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

    har_stats["filename"]=filename

    return har_stats
