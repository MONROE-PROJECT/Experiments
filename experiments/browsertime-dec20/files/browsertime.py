#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Mohammad Rajiullah
# Date: August 2020
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""
Browsertime uses Selenium NodeJS to drive the browser (latest version of firefox and chrome). 
It starts the browser, load a URL, executes configurable Javascripts to collect metrics, collect a HAR file.
"""

import sys, getopt
import time, os
import fileinput
import datetime
from dateutil.parser import parse
import json
import zmq
import re
import netifaces
import time
import subprocess
import shlex
import socket
import struct
import random
import psutil
import netifaces as ni
from subprocess import check_output, CalledProcessError
from multiprocessing import Process, Manager
from flatten_json import flatten

import shutil
import stat

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
browser_kind=''
h1='http://'
h1s='https://'
h2='https://'
quic='https://'
http3='https://'
current_directory =''
har_directory =''

first_run=1
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
	"dataid": "MONROE.EXP.HEADLESS.BROWSERTIME",
	"nodeid": "fake.nodeid",
	"meta_grace": 120,  # Grace period to wait for interface metadata
	"exp_grace": 120,  # Grace period before killing experiment
	"ifup_interval_check": 6,  # Interval to check if interface is up
	"time_between_experiments": 5,
	"verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
	"resultdir": "/monroe/results/",
        "flatten_delimiter": '.',
	"modeminterfacename": "InternalInterface",
        "urls": [
	     "www.youtube.com",
             "www.instagram.com",
	     "www.google.com",
	     "www.myshopify.com",
	     "www.google.com.hk",
	     "www.google.co.in",
             "www.google.co.jp",	
             "www.google.com.br",	
	     "www.facebook.com"
       ],
        "http_protocols":["h2","h1s","http3"],
        "browsers":["chrome","firefox"],
        "iterations": 1,
	"allowed_interfaces": ["ens160", "ens192", "eth0","op0","op1","op2"],  # Interfaces to run the experiment on
	"interfaces_without_metadata": ["eth0", "ens160", "ens192"]  # Manual metadata on these IF
	}

def get_recursively(search_dict, field):
    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key which consists
    of the field provided.
    Adapted from : https://stackoverflow.com/a/20254842
    """
    fields_found = []

    for key, value in search_dict.iteritems():
        if field in key:
            fields_found.append(key)
            search_dict[key.replace(field, '_')] = search_dict.pop(key)
        elif isinstance(value, dict):
            results = get_recursively(value, field)
            for result in results:
                fields_found.append(result)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    more_results = get_recursively(item, field)
                    for another_result in more_results:
                        fields_found.append(another_result)
    return fields_found


def check_system():
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory()[2]
    disk_percent = psutil.disk_usage('/')[3]
    disk_percent_2 = psutil.disk_usage('/dev/shm/')[3]
    response = "Current disk_percent is %s percent.  " % disk_percent
    response = "Current shared memory disk_percent is %s percent.  " % disk_percent_2
    response += "Current CPU utilization is %s percent.  " % cpu_percent
    response += "Current memory utilization is %s percent. " % memory_percent
    print response

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

def check_dns(dns_list):
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


def run_exp(meta_info, expconfig, url,count):
	"""Seperate process that runs the experiment and collect the ouput.

	Will abort if the interface goes down.
	"""
	ifname = meta_info[expconfig["modeminterfacename"]]

	#url=url_list[index]

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

	if not os.path.exists('web-res'):
		os.makedirs('web-res')

	print "Clearing temp directories.."
	root="/tmp/"
	try:
		for item in os.listdir(root):
			if os.path.isdir(os.path.join(root, item)):
				print "/tmp/"+item
				if "tmp" in item or "Chrome" in item:
					print "Deleting {}".format(item)
					shutil.rmtree("/tmp/"+item)
	except OSError, e:  ## if failed, report it back to the user ##
		print ("Error: %s - %s." % (e.filename,e.strerror))

	har_stats={}

	#check_system()

	if browser_kind=="chrome":
		har_stats=run_experiment.browse_chrome(ifname,url,getter_version)
	else:
		if (getter_version !="quic"):
			har_stats=run_experiment.browse_firefox(ifname,url,getter_version)

	if bool(har_stats):
		shutil.rmtree('web-res')
	#har_stats["browserScripts"][0]["timings"].pop('resourceTimings')
	else:
		return
	try:
		har_stats["ping_max"]=float(ping_max)
		har_stats["ping_avg"]=float(ping_avg)
		har_stats["ping_min"]=float(ping_min)
		har_stats["ping_exp"]=True
	except Exception:
		print("Ping info is not available")
		har_stats["ping_exp"]=False

	har_stats["url"]=url
	#har_stats["Protocol"]=getter_version
	har_stats["DataId"]= expconfig['dataid']
	har_stats["DataVersion"]= expconfig['dataversion']
	har_stats["NodeId"]= expconfig['nodeid']
	har_stats["Timestamp"]= time.time()
	try:
		har_stats["Iccid"]= meta_info["ICCID"]
	except Exception:
		print("ICCID info is not available")
	#try:
	#	har_stats["Operator"]= meta_info["Operator"]
	#except Exception:
	#	print("Operator info is not available")
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

		if har_stats["IMSIMCCMNC"]==24001:
			har_stats["Ops"]="Telia (SE)"
		if har_stats["IMSIMCCMNC"]==24201:
			har_stats["Ops"]="Telenor (NO)"
		if har_stats["IMSIMCCMNC"]==24008:
			har_stats["Ops"]="Telenor (SE)"
		if har_stats["IMSIMCCMNC"]==24002:
			har_stats["Ops"]="Tre (SE)"
		if har_stats["IMSIMCCMNC"]==22201:
			har_stats["Ops"]="TIM (IT)"
		if har_stats["IMSIMCCMNC"]==21404:
			har_stats["Ops"]="Yoigo (ES)"

		if har_stats["IMSIMCCMNC"]==22210:
			har_stats["Ops"]="Vodafone (IT)"
		if har_stats["IMSIMCCMNC"]==24202:
			har_stats["Ops"]="Telia (NO)"

		if har_stats["IMSIMCCMNC"]==24214:
			har_stats["Ops"]="ICE (NO)"
		if har_stats["IMSIMCCMNC"]==22288:
			har_stats["Ops"]="Wind (IT)"
		if har_stats["IMSIMCCMNC"]==21403:
			har_stats["Ops"]="Orange (ES)"

		if har_stats["IMSIMCCMNC"]==24001:
			har_stats["Country"]="SE"
		if har_stats["IMSIMCCMNC"]==24201:
			har_stats["Country"]="NO"
		if har_stats["IMSIMCCMNC"]==24008:
			har_stats["Country"]="SE"
		if har_stats["IMSIMCCMNC"]==24002:
			har_stats["Country"]="SE"
		if har_stats["IMSIMCCMNC"]==22201:
			har_stats["Country"]="IT"
		if har_stats["IMSIMCCMNC"]==21404:
			har_stats["Country"]="ES"

		if har_stats["IMSIMCCMNC"]==22210:
			har_stats["Country"]="IT"
		if har_stats["IMSIMCCMNC"]==24202:
			har_stats["Country"]="NO"

		if har_stats["IMSIMCCMNC"]==24214:
			har_stats["Country"]="NO"
		if har_stats["IMSIMCCMNC"]==22288:
			har_stats["Country"]="IT"
		if har_stats["IMSIMCCMNC"]==21403:
			har_stats["Country"]="ES"


	except Exception:
		print("IMSIMCCMNC info is not available")
	try:
		har_stats["NWMCCMNC"]=meta_info["NWMCCMNC"]
	except Exception:
		print("NWMCCMNC info is not available")
	har_stats["SequenceNumber"]= count



	with open('/tmp/'+str(har_stats["NodeId"])+'_'+str(har_stats["DataId"])+'_'+str(har_stats["Timestamp"])+'.json', 'w') as outfile:
		json.dump(har_stats, outfile)
	print "Saving browsing information ..."
	if expconfig['verbosity'] > 2:
		print("Done with Browser: {}, HTTP protocol: {}, url: {}, PLT: {}".format(har_stats["browser"],har_stats["protocol"],har_stats["url"], har_stats["pageLoadTime"]))
	if not DEBUG:
		#print har_stats["browser"],har_stats["Protocol"],har_stats["url"]
		print("Done with Browser: {}, HTTP protocol: {}, url: {}, PLT: {}".format(har_stats["browser"],har_stats["protocol"],har_stats["url"], har_stats["pageLoadTime"]))
		if first_run==0:
			monroe_exporter.save_output(har_stats, expconfig['resultdir'])



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


def create_exp_process(meta_info, expconfig,url,count):
	process = Process(target=run_exp, args=(meta_info, expconfig,url,count))
	process.daemon = True
	return process


if __name__ == '__main__':
	"""The main thread control the processes (experiment/metadata))."""

	os.system('clear')
	current_directory = os.path.dirname(os.path.abspath(__file__))

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
		browsers=EXPCONFIG['browsers']
		if_without_metadata = EXPCONFIG['interfaces_without_metadata']
		meta_grace = EXPCONFIG['meta_grace']
		#exp_grace = EXPCONFIG['exp_grace'] + EXPCONFIG['time']
		exp_grace = EXPCONFIG['exp_grace']
		ifup_interval_check = EXPCONFIG['ifup_interval_check']
		time_between_experiments = EXPCONFIG['time_between_experiments']
		flatten_delimiter = str(EXPCONFIG['flatten_delimiter'])
		verbosity=EXPCONFIG['verbosity']
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
	print "Randomizing the url lists .."
	random.shuffle(urls)


	# checking all the available interfaces
	try:
		for ifname in allowed_interfaces:
			if ifname not in open('/proc/net/dev').read():
				allowed_interfaces.remove(ifname)
	except Exception as e:
		print "Cannot remove nonexisting interface {}".format(e)
		raise e


	for ifname in allowed_interfaces:
		print "Caches from other operators"

		startDir="/opt/monroe/"
		for item in os.listdir(startDir):
			folder = os.path.join(startDir, item)
			if os.path.isdir(folder) and "cache" in item:
				try:
					shutil.rmtree(folder)
				except:
					print "Exception ",str(sys.exc_info())

		first_run=1
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
			check_dns(dns_list)


		if EXPCONFIG['verbosity'] > 1:
			print "Starting experiment"

		for url in urls:
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
				elif protocol == 'quic':
					getter = quic
					getter_version = 'QUIC'
				elif protocol == 'http3':
					getter = http3
					getter_version = 'HTTP3'
				else:
					print 'Unknown HTTP Scheme: <HttpMethod:h1/h1s/h2/quic/Http3>'
					sys.exit()
				random.shuffle(browsers)
				for browser in browsers:
					browser_kind=browser
					if browser == "firefox" and protocol == "quic":
						continue
                                        #elif browser == "chrome" and protocol == "quic" and (url not in quic_urls and url !="www.youtube.com/watch?v=544vEgMiMG0"):
                                         #       continue
                                        #elif protocol != "quic" and browser == "firefox" and url in quic_urls:
                                         #   continue
					for run in range(start_count, iterations):
						# Create a experiment process and start it
						print "Browsing {} with {} browser and {} protocol".format(url,browser,protocol)
						start_time_exp = time.time()
						exp_process = exp_process = create_exp_process(meta_info, EXPCONFIG, url,run+1)
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
					first_run=0
		if meta_process.is_alive():
			meta_process.terminate()
		if EXPCONFIG['verbosity'] > 1:
			print ("Interfaces {} "
				"done, exiting").format(ifname)
		first_run=1
