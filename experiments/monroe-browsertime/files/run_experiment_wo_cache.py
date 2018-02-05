import os
import errno
import sys
import filecmp
import shutil
import subprocess
import glob
import json
from subprocess import check_output, CalledProcessError



def browse_chrome(iface,url,getter_version):

	print "Cache folder for chrome {}",format(folder_name)
	har_stats={}
	loading=True
	try:
		if getter_version == 'HTTP1.1/TLS':
			cmd=['bin/browsertime.js',"https://"+str(url), 
				'--skipHar','-n','1','--resultDir','web-res',
				'--chrome.args', 'no-sandbox','--chrome.args', 'disable-http2',  
				'--userAgent', '"Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75  Mobile Safari/537.36"']
			output=check_output(cmd)
		else:
			cmd=['bin/browsertime.js',"https://"+str(url), 
				'--skipHar','-n','1','--resultDir','web-res',
				'--chrome.args', 'no-sandbox','--chrome.args', 
				'--userAgent', '"Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75  Mobile Safari/537.36"']
			output=check_output(cmd)
		with open('web-res/browsertime.json') as data_file:    
			har_stats = json.load(data_file)
			har_stats["browser"]="Chrome"
			har_stats["protocol"]=getter_version
			har_stats["cache"]=1
	except CalledProcessError as e:
		if e.returncode == 28:
			print "Time limit exceeded"
			loading=False
	
	if loading:
		return har_stats


def browse_firefox(iface,url,getter_version):

	har_stats={}
	loading=True
	try:
		if getter_version == 'HTTP1.1/TLS':
			cmd=['bin/browsertime.js','-b',"firefox","https://"+str(url), 
				'--skipHar','-n','1','--resultDir','web-res',
				'--firefox.preference', 'network.http.spdy.enabled:false', 
				'--firefox.preference', 'network.http.spdy.enabled.http2:false', 
				'--firefox.preference', 'network.http.spdy.enabled.v3-1:false',  
				'--userAgent', '"Mozilla/5.0 (Android 4.4; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0"']
			output=check_output(cmd)

		else:
			cmd=['bin/browsertime.js','-b',"firefox","https://"+str(url), 
				'--skipHar','-n','1','--resultDir','web-res',
				'--userAgent', '"Mozilla/5.0 (Android 4.4; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0"']
			output=check_output(cmd)
			
		with open('web-res/browsertime.json') as data_file:    
			har_stats = json.load(data_file)
			har_stats["browser"]="Firefox"
			har_stats["cache"]=0
	
	except CalledProcessError as e:
		if e.returncode == 28:
			print "Time limit exceeded"
			loading=False
	
	#print har_stats["browserScripts"][0]["timings"]["pageTimings"]["pageLoadTime"]
	if loading:
		return har_stats
