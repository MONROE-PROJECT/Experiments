import os
import sys
import shutil
import subprocess
import json
from subprocess import check_output, CalledProcessError


domains=["facebook","google","wikipedia","instagram","linkedin","yahoo","youtube","theguardian","ebay","nytimes"]

def run_experiment(iface,url, protocol, browser,no_cache):
	for item in domains:
		if item in url.split("/")[0]:
			url_short=item
	folder_name=iface+"-"+url_short+"-"+protocol+"-"+browser 
	print 'user-data-dir=/opt/monroe/'+folder_name+"/"
	har_stats={}
	if no_cache=="1":
		print "Will not use any cache"
		if browser=="chrome":
			#empty /opt/monroe/iface-url-protocol-browser/ folder
			if os.path.isdir(folder_name):
				print "clearing cache"
				for the_file in os.listdir(folder_name):
    				    file_path = os.path.join(folder_name, the_file)
    				    try:
        				if os.path.isfile(file_path):
            				    os.unlink(file_path)
        				elif os.path.isdir(file_path): shutil.rmtree(file_path)
    				    except Exception as e:
        				print(e)
        	        try:
				cmd=['bin/browsertime.js',"https://"+str(url), 
                    		'--skipHar','-n','1','--resultDir','web-res',
                    		'--chrome.args', 'no-sandbox', 
                    		'--chrome.args', 'disable-http2',  
                    		'--chrome.args', 'user-data-dir=/opt/monroe/'+folder_name+"/",
                    		'--userAgent', '"Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75  Mobile Safari/537.36"']
            	                output=check_output(cmd)
            	                with open('web-res/browsertime.json') as data_file:    
                	            har_stats = json.load(data_file)
                                    har_stats["browser"]="Chrome"
                                    har_stats["cache"]=0
                        except CalledProcessError as e:
        	            if e.returncode == 28:
                                print "Time limit exceeded"
	else:
		print "cache will be used"
		if browser=="chrome":
        	        try:
				cmd=['bin/browsertime.js',"https://"+str(url), 
                    		'--skipHar','-n','1','--resultDir','web-res',
                    		'--chrome.args', 'no-sandbox', 
                    		'--chrome.args', 'disable-http2',  
                    		'--chrome.args', 'user-data-dir=/opt/monroe/'+folder_name+"/",
                    		'--userAgent', '"Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75  Mobile Safari/537.36"']
            	                output=check_output(cmd)
            	                with open('web-res/browsertime.json') as data_file:    
                	            har_stats = json.load(data_file)
                                    har_stats["browser"]="Chrome"
                                    har_stats["cache"]=0
                        except CalledProcessError as e:
        	            if e.returncode == 28:
                                print "Time limit exceeded"
		
	print har_stats["browserScripts"][0]["timings"]["pageTimings"]["pageLoadTime"]

run_experiment("op0","facebook.com/telia/","h1s","chrome",sys.argv[1])
