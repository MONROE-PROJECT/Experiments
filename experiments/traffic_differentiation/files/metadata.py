#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Ali Safari Khatouni
# Date: October 2017
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

import json
import zmq
import netifaces
import sys
import socket
from time import sleep, time, mktime
from os import mkdir,rename,listdir,remove,system,makedirs
from os.path import isfile,join,isdir,getsize

Default_conf = {
		"zmqport": "tcp://172.17.0.1:5556",
		"modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
		"dataversion": 3,
		"nodeid": "fake.nodeid",
		"rsync_dir" : "/monroe/results/",
		"shared_dir" : "/monroe/tstat/",
		"tstat_dir" : "/opt/monroe/monroe-mplane/tstat-conf/",
		"log_dir" : "/tmp/", 
		"verbosity": 2,  
		"modeminterfacename": "InternalInterface",
		"disabled_interfaces": ["lo",
								"metadata",
								"wlan0",
								"docker0",
								"eth0" ],  # Interfaces to NOT run the experiment on
		"interfaces_without_metadata": []  # "wlp2s0" Manual metadata on these IF
		}



Servers = {
		"NO": "128.39.37.161", 
		"SE": "130.243.27.222", 
		"IT": "130.192.181.137",
		"UK": "139.133.232.22",
		"ES": "163.117.253.6",
		"DE": "141.40.254.133"}

Nodes = { 
		"285": "ES",
		"298": "NO",
		"302": "DE",
		"322": "IT",
		"323": "IT",
		"332": "IT",
		"333": "IT",
		"328": "NO",
		"329": "ES",
		"496": "SE",
		"497": "SE",
		"517": "NO",
		"518": "UK",
		"519": "DE",
		"549": "UK",
		}


"""
FIXME list of ICCID for TBA
"""

Operators = { 
			"Vodafone-ES" :  "893456",
			"Movistar-ES" : "893407",
			"Orange-ES" : "893401", 
			"Telenor-NO" : "894700", 
			"Telia-NO": "894708", 
			"EE-UK" : ["89443034", "89446034"],
			"Vodafone-UK" : "8944100", 
			"3-IT" : "893999432", 
			"TIM-IT" : "893901000", 
			"Vodafone-IT" : "89391042", 
			"O2-DE" : "89492271728054",
			"Telekom-DE" : "8949020000136896",
			"Vodafone-DE" : "894920",
			"Telia-SE" : "894601", 
			"3-SE" : "8946071", 
			"Telenor-SE" : "894608500", 
			}

log_fp=open("python.log",'w')


# Helper functions
def check_if(EXPCONFIG):
	"""Check if interface is up and have got an IP address."""
	interface_list=netifaces.interfaces()
	output=[]
	for i in interface_list:
		if not (i in EXPCONFIG["disabled_interfaces"] or netifaces.AF_INET not in netifaces.ifaddresses(i)) :
			output.append(i)
	return output

def metadata(EXPCONFIG):
	"""
		the ZeroMQ socket as a subscriber.
		Will listen till get an update from all inetrfaces.
	"""
	interface_list=check_if(EXPCONFIG)
	for i in  EXPCONFIG["interfaces_without_metadata"]:
		if i in interface_list:
			fp=open(i+".metadata","w")
			fp.write("{'InternalInterface' : '%s'}"%i)
			fp.close()
			interface_list.remove(i)
	context = zmq.Context()
	socket = context.socket(zmq.SUB)
	socket.connect(EXPCONFIG['zmqport'])
	socket.setsockopt(zmq.SUBSCRIBE, EXPCONFIG['modem_metadata_topic'])
	log_fp.write (str(interface_list))
	while len(interface_list)>0:
		metadata={}
		data = socket.recv()
		try:
			ifinfo = json.loads(data.split(" ", 1)[1])
			if (EXPCONFIG["modeminterfacename"] in ifinfo ):
				# In place manipulation of the reference variable
				dic_info = {}
				dic_info["NodeId"]=eval(open("/monroe/config","r").read())["nodeid"]
				for key, value in ifinfo.iteritems():
					try :
						k=str(key.encode("utf-8"))
						if type(value) is not int and type(value) is not float:   
							v=str(value.encode("utf-8"))
						else:
							v=value  
					except Exception as e:
						log_fp.write ("encoding error "+str(e))
						v="None"  
					dic_info[k]=v


				log_fp.write(str (dic_info))
				log_fp.write(str (EXPCONFIG))
				log_fp.write(str (interface_list))

				if check_meta(dic_info,EXPCONFIG,interface_list) :
					fp=open(dic_info[EXPCONFIG["modeminterfacename"]]+".metadata","w")
					fp.write(str(dic_info))
					fp.close()
					log_fp.write("remove "+ str(dic_info[EXPCONFIG["modeminterfacename"]]) )
					interface_list.remove(str(dic_info[EXPCONFIG["modeminterfacename"]]))
		except Exception as e:
			pass
	return 0

def check_meta(info, EXPCONFIG,interface_list):
	"""Check if we have recieved required information."""
	if (EXPCONFIG["modeminterfacename"] in info and
			"Operator" in info and
			"Timestamp" in info and
			"ICCID" in info and
			"NWMCCMNC" in info and
			"IMSIMCCMNC" in info and 
			"CID" in info ): 
		if (info ["ICCID"] != "None" and 
			info[EXPCONFIG["modeminterfacename"]] != "None" and
			info[EXPCONFIG["modeminterfacename"]] in interface_list and
			info["NWMCCMNC"] != "None" and
			info["IMSIMCCMNC"] != "None" and
			info["CID"] != "None" ):
			set_servers(info,EXPCONFIG)
			return True
	return False

#"operator":"TIM","country":"IT"
def set_servers(info,EXPCONFIG):
	#Set the servers 
	container_config=eval(open("/monroe/config","r").read())
	nodeid=container_config["nodeid"]
	server_string=""
	op_index=container_config["operator"]+"-"+container_config["country"]
	log_fp.write (str(op_index)) 
	if isinstance(Operators[op_index],basestring):
		if info ["ICCID"].startswith(Operators[op_index]):
			if container_config["country"]==Nodes[nodeid]:
				server_string=Servers[container_config["country"]]+" "
			else:
				server_string=Servers[container_config["country"]]+" "+ Servers[Nodes[nodeid]]
	elif type(Operators[op_index]) is list:
		for e in Operators[op_index]:
			if info ["ICCID"].startswith(e):
				if container_config["country"]==Nodes[nodeid]:
					server_string=Servers[container_config["country"]]+" "
					break
				else:
					server_string=Servers[container_config["country"]]+" "+Servers [Nodes[nodeid]]
					break
	else:
		log_fp.write ("Unkown type for operator")
	log_fp.write (str(nodeid)) 
	log_fp.write (str(server_string)) 
	log_fp.write (op_index) 
	log_fp.write (str(info)) 
	log_fp.write (str(EXPCONFIG)) 
	log_fp.write (str(container_config["country"])) 
	log_fp.write (str(container_config)) 
	if len(server_string)>0:
		fp = open(info[EXPCONFIG["modeminterfacename"]]+".servers","w")
		fp.write(server_string)
		fp.close()

if __name__ == '__main__':
	metadata(Default_conf)