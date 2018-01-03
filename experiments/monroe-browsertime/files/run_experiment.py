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
            #linkto=os.readlink(s)
            #if not os.path.exists(d
            #if not filecmp.cmp(s,d):
                #os.symlink(linkto,d)
        else:
            if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                shutil.copy2(s, d)


domains=["facebook","google","wikipedia","instagram","linkedin","yahoo","youtube","theguardian","ebay","nytimes"]

original=["key3.db","chrome","logins.json","cookies.sqlite"]


def browse_chrome(iface,url,cache_off,getter_version):
	
	if "1.1" in getter_version:
		protocol="h1s"
	else:
		protocol="h2"

	for item in domains:
		if item in url.split("/")[0]:
			url_short=item
	folder_name="cache-"+iface+"-"+url_short+"-"+protocol+"-"+"chrome"
        print "Cache folder for chrome {}",format(folder_name)
	har_stats={}
	loading=True
        if cache_off==1:
		        print "Will not use any cache"
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
				if getter_version == 'HTTP1.1/TLS':
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
                                    		har_stats["protocol"]=getter_version
                                    		har_stats["cache"]=0
				else:
					cmd=['bin/browsertime.js',"https://"+str(url), 
                    				'--skipHar','-n','1','--resultDir','web-res',
                    				'--chrome.args', 'no-sandbox', 
                    				'--chrome.args', 'user-data-dir=/opt/monroe/'+folder_name+"/",
                    				'--userAgent', '"Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75  Mobile Safari/537.36"']
            	                	output=check_output(cmd)
            	                	with open('web-res/browsertime.json') as data_file:    
                	            		har_stats = json.load(data_file)
                                    		har_stats["browser"]="Chrome"
                                    		har_stats["protocol"]=getter_version
                                    		har_stats["cache"]=0
					
                        except CalledProcessError as e:
        	            if e.returncode == 28:
                                print "Time limit exceeded"
				loading=False
	else:
		        print "cache will be used"
        	        try:
				if getter_version == 'HTTP1.1/TLS':
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
                                    		har_stats["protocol"]=getter_version
                                    		har_stats["cache"]=1
				else:
					cmd=['bin/browsertime.js',"https://"+str(url), 
                    				'--skipHar','-n','1','--resultDir','web-res',
                    				'--chrome.args', 'no-sandbox', 
                    				'--chrome.args', 'user-data-dir=/opt/monroe/'+folder_name+"/",
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
	#print har_stats["browserScripts"][0]["timings"]["pageTimings"]["pageLoadTime"]
	

def browse_firefox(iface,url, cache_off,getter_version):
	if "1.1" in getter_version:
		protocol="h1s"
	else:
		protocol="h2"

	for item in domains:
		if item in url.split("/")[0]:
			url_short=item
	folder_name="cache-"+iface+"-"+url_short+"-"+protocol+"-"+"firefox"
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
        common_cache_folder="/opt/monroe/profile_moz/"
	#delete the common cache folder
        if os.path.exists(common_cache_folder):	
		try:
                        print "Deleting the common cache dir {}".format(common_cache_folder)
			shutil.rmtree(common_cache_folder)
		except:
            		print "Exception ",str(sys.exc_info())
	if cache_off==1:
		        print "Will not use any cache"
        	        try:
				cmd=['bin/browsertime.js','-b',"firefox","https://"+str(url), 
                    		'--skipHar','-n','1','--resultDir','web-res',
                    		'--firefox.preference', 'network.http.spdy.enabled:false', 
                    		'--firefox.preference', 'network.http.spdy.enabled.http2:false', 
                    		'--firefox.preference', 'network.http.spdy.enabled.v3-1:false',  
                    		'--userAgent', '"Mozilla/5.0 (Android 4.4; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0"']
            	                output=check_output(cmd)
            	                with open('web-res/browsertime.json') as data_file:    
                	            har_stats = json.load(data_file)
                                    har_stats["browser"]="Firefox"
                                    har_stats["cache"]=0
				#copy /opt/monroe/profile_moz to   folder
                                copytree("/opt/monroe/profile_moz","/opt/monroe/"+folder_name+"/")
                        except CalledProcessError as e:
        	            if e.returncode == 28:
                                print "Time limit exceeded"
				loading=False
	else:
	                print "cache will be used"
        	        try:
				#copy the folder contents to the firefoxprofile
				try:
     					#for files in os.listdir('/opt/monroe/'+folder_name+'/'):
					#	shutil.copy(files,'/opt/monroe/browsersupport/firefox-profile/')
                                    print "Copy the cache dir {} to the profile dir".format(folder_name)
                                        
                                    copytree("/opt/monroe/"+folder_name+"/","/opt/monroe/browsersupport/firefox-profile/")
				except shutil.Error as e:
					print('Directory not copied. Error: %s' % e)
				except OSError as e:
					print('Directory not copied. Error: %s' % e)
				cmd=['bin/browsertime.js','-b',"firefox","https://"+str(url), 
                    		'--skipHar','-n','1','--resultDir','web-res',
                    		'--firefox.preference', 'network.http.spdy.enabled:false', 
                    		'--firefox.preference', 'network.http.spdy.enabled.http2:false', 
                    		'--firefox.preference', 'network.http.spdy.enabled.v3-1:false',  
                    		'--userAgent', '"Mozilla/5.0 (Android 4.4; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0"']
            	                output=check_output(cmd)
            	                with open('web-res/browsertime.json') as data_file:    
                	            har_stats = json.load(data_file)
                                    har_stats["browser"]="Firefox"
                                    har_stats["cache"]=1
				#clear the firefox-profile directory
			        for CleanUp in glob.glob("/opt/monroe/browsersupport/firefox-profile/*"):
                                	if CleanUp.split("/")[-1] not in original:
                                                if os.path.isdir(CleanUp):
                                                    shutil.rmtree(CleanUp)
                                                else:
						    os.remove(CleanUp)	
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
            return har_stats
