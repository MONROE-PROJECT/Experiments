import os
import errno
import sys
import filecmp
import shutil
import subprocess
import glob
import json
from subprocess import check_output, CalledProcessError

def copytree(src, dst, symlinks=True, ignore=None):
	if not os.path.exists(dst):
		os.makedirs(dst)
	for item in os.listdir(src):
		s = os.path.join(src, item)
		d = os.path.join(dst, item)
		if os.path.isdir(s):
			copytree(s, d, symlinks, ignore)
		elif os.path.islink(s):
			pass
		else:
			if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
				shutil.copy2(s, d)

def process_har_files():
    objs=[]
    pageSize=0
    processed_har={}
    protocols={}
    try:
        with open("web-res/browsertime.har") as f:
            har=json.load(f)
            num_of_objects=0
            for entry in har["log"]["entries"]:
                try:
                    obj={}
		    if entry["response"]["bodySize"] is not None and entry["response"]["headersSize"] is not None:
        	            pageSize=pageSize+entry["response"]["bodySize"]+entry["response"]["headersSize"]
		    request_protocol=entry["request"]["httpVersion"]
		    response_protocol=entry["response"]["httpVersion"]
                    if response_protocol in protocols:
			protocols[response_protocol] +=1
		    else:
                        protocols[response_protocol]=1
                    num_of_objects=num_of_objects+1
                except KeyError:
                    pass
	    har["used_protocols"]=protocols
            har["NumObjects"]=num_of_objects
            har["PageSize"]=pageSize
            return har
    except IOError:
        print "HAR file not found ..."




def browse_chrome(iface,url,getter_version):

	if "1.1" in getter_version:
		protocol="h1s"
	elif getter_version=="HTTP2":
		protocol="h2"
	elif getter_version=="QUIC":
		protocol="quic"
	
	folder_name="cache-"+iface+"-"+protocol+"-"+"chrome"
	print "Cache folder for chrome {}",format(folder_name)
	har_stats={}
	loading=True
	try:
		if getter_version == 'HTTP1.1/TLS':
			cmd=['/usr/src/app/bin/browsertime.js',"https://"+str(url), 
				'-n','1','--resultDir','web-res',
				'--chrome.args', 'no-sandbox','--chrome.args', 'disable-http2',  
				'--chrome.args', 'user-data-dir=/opt/monroe/'+folder_name+"/",
				'--userAgent', '"Mozilla/5.0 (Linux; Android 10; SM-G950F Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83  Mobile Safari/537.36"']
			#output=check_output(cmd)
			output=check_output(" ".join(cmd), shell=True)
		elif getter_version=="HTTP2":
			cmd=['/usr/src/app/bin/browsertime.js',"https://"+str(url), 
				'-n','1','--resultDir','web-res',
				'--chrome.args', 'no-sandbox','--chrome.args', 'user-data-dir=/opt/monroe/'+folder_name+"/",
				'--userAgent', '"Mozilla/5.0 (Linux; Android 10; SM-G950F Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83  Mobile Safari/537.36"']
			#output=check_output(cmd)
			output=check_output(" ".join(cmd), shell=True)
		elif getter_version=="QUIC":
			cmd=['/usr/src/app/bin/browsertime.js',"https://"+str(url), 
				'-n','1','--resultDir','web-res',
				'--chrome.args','enable-quic',
				'--chrome.args', 'no-sandbox','--chrome.args', 'user-data-dir=/opt/monroe/'+folder_name+"/",
				'--userAgent', '"Mozilla/5.0 (Linux; Android 10; SM-G950F Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83  Mobile Safari/537.36"']
			output=check_output(" ".join(cmd), shell=True)
                print "Processing the HAR files ..."
		har={}
                try:
		    with open('web-res/browsertime.json') as data_file:    
                        	har["browsertime-json"] = json.load(data_file)
                        	har["browsertime-json"][0].pop('statistics',None)#These fileds are only relevant when multiple runs are done and a statistics is required
				har['pageLoadTime']=har["browsertime-json"][0]["browserScripts"][0]["timings"]['pageTimings']['pageLoadTime']

                except IOError:
                    print "No output found"

                har["browsertime-har"]=process_har_files()
		har["browser"]="Chrome"
		har["protocol"]=getter_version
		#har_stats["cache"]=1

	except CalledProcessError as e:
		if e.returncode == 28:
			print "Time limit exceeded"
			loading=False
	
	if loading:
		return har


def browse_firefox(iface,url,getter_version):
        browser_cache="/usr/src/app/browsersupport/firefox-profile"
        if not os.path.exists("/opt/monroe/basic_browser_repo"):
                 try:
			fname="/opt/monroe/basic_browser_repo"
                        print "Creating the dir {}".format("fname")
                        os.makedirs(fname)
                 except OSError as e:
                        if e.errno != errno.EEXIST:
                                raise
        	 try:
                	copytree("/usr/src/app/browsersupport/",fname)
		 except shutil.Error as e:
                        print('Directory not copied. Error: %s' % e)
		
	if "1.1" in getter_version:
		protocol="h1s"
	else:
		protocol="h2"

	folder_name="cache-"+iface+"-"+protocol+"-"+"firefox"
	print "Cache folder for firefox {}",format(folder_name)
	har_stats={}
	loading=True
	#create this directory if it doesn't exist
	if not os.path.exists(folder_name):
		try:
			print "Creating the cache dir {}".format(folder_name)
			os.makedirs(folder_name)
		except OSError as e:
			if e.errno != errno.EEXIST:
				raise
	else:
		print "Copy the cache dir {} to the profile dir".format(folder_name)
		try:
			copytree("/opt/monroe/"+folder_name+"/",browser_cache)
		except shutil.Error as e:
			print('Directory not copied. Error: %s' % e)
		except OSError as e:
			print('Directory not copied. Error: %s' % e)
	common_cache_folder="/opt/monroe/profile_moz/"
	#delete the common cache folder
	if os.path.exists(common_cache_folder):	
		try:
			print "Deleting the common cache dir {}".format(common_cache_folder)
			shutil.rmtree(common_cache_folder)
		except:
			print "Exception ",str(sys.exc_info())
        print os.listdir("/usr/src/app/browsersupport/firefox-profile")
	try:
		if getter_version == 'HTTP1.1/TLS':
			cmd=['/usr/src/app/bin/browsertime.js','-b',"firefox","https://"+str(url), 
				'-n','1','--resultDir','web-res',
				'--firefox.preference', 'network.http.spdy.enabled:false', 
				'--firefox.preference', 'network.http.spdy.enabled.http2:false', 
				'--firefox.preference', 'network.http.spdy.enabled.v3-1:false',  
				'--userAgent', '"Mozilla/5.0 (Android 10; Mobile; rv:80.0) Gecko/20100101 Firefox/80.0"']
			#output=check_output(cmd)
			output=check_output(" ".join(cmd), shell=True)

		else:
			cmd=['/usr/src/app/bin/browsertime.js','-b',"firefox","https://"+str(url), 
				'-n','1','--resultDir','web-res',
				'--userAgent', '"Mozilla/5.0 (Android 10; Mobile; rv:80.0) Gecko/20100101 Firefox/80.0"']
			#output=check_output(cmd)
			output=check_output(" ".join(cmd), shell=True)
		#print  os.listdir("web-res")	
                har={}
                try:
		    with open('web-res/browsertime.json') as data_file:    
			        har["browsertime-json"] = json.load(data_file)
				har['pageLoadTime']=har["browsertime-json"][0]["browserScripts"][0]["timings"]['pageTimings']['pageLoadTime']

                except IOError:
                    print "No output found"
                har["browsertime-har"]=process_har_files()
                har["har"]=process_har_files()
		har["browser"]="Firefox"
		har["protocol"]=getter_version
		#har_stats["cache"]=0
                #clear the copied contents from /usr/src/app/browsersupport/firefox-profile folder
	        if os.path.exists(browser_cache):	
		    try:
			print "Deleting the browser cache dir {}".format(browser_cache)
			shutil.rmtree(browser_cache)
		    except:
			print "Exception ",str(sys.exc_info())
	        if os.path.exists("/opt/monroe/basic_browser_repo"):	
		    try:
			copytree("/opt/monroe/basic_browser_repo","/usr/src/app/browsersupport/")
		    except shutil.Error as e:
			print('Directory not copied. Error: %s' % e)
		    except OSError as e:
			print('Directory not copied. Error: %s' % e)
                else:
                    print "STRANGE!!!!"
		#copy /opt/monroe/profile_moz to   folder
		try:
			#for files in os.listdir('/opt/monroe/profile_moz'):
			#	shutil.copy(files,'/opt/monroe/'+folder_name+'/')
			copytree("/opt/monroe/profile_moz","/opt/monroe/"+folder_name+"/")
		except shutil.Error as e:
			print('Directory not copied. Error: %s' % e)
		except OSError as e:
			print('Directory not copied. Error: %s' % e)
	
	except CalledProcessError as e:
		if e.returncode == 28:
			print "Time limit exceeded"
			loading=False
	
	#print har_stats["browserScripts"][0]["timings"]["pageTimings"]["pageLoadTime"]
	if loading:
		return har
