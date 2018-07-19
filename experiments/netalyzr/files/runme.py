#!/usr/bin/python
import json
import subprocess
import logging
from pyroute2 import IPDB
import sys

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("runme")

def add_dns(interface):
    str = ""
    try:
        with open('/dns') as dnsfile:

            dnsdata = dnsfile.readlines()
            dnslist = [ x.strip() for x in dnsdata ]
            for item in dnslist:
                if interface in item:
                    str += item.split('@')[0].replace("server=", "nameserver ")
                    str += "\n"
        with open("/etc/resolv.conf", "w") as f:
            f.write(str)
    except:
        print("Could not find DNS file")
    return str


def main():
    ip = IPDB()
    s = set([interface.ifname for interface in ip.interfaces.values()])
    
    try:
         s.remove('lo')
         s.remove('metadata')
    except:
         logger.error("Metadata or lo not found!\n")
    
    try:
        with open('/monroe/config') as configfile:
            config  = json.load(configfile)
            nodeid = config['nodeid']
    except:
        nodeid = 'could-not-get-id'
    try:
        with open('/monroe/config') as configfile:
            config  = json.load(configfile)
            operator = config['operator']
    except:
       operator = 'N/A'


    subprocess.call(['mkdir', '/tmp/res/'])
    result_files=[]
    
    for item in s:
        if item in ['op0', 'op1', 'op2']:
            logger.debug("Running on interface: " + item)   
            try:
               subprocess.call(['route', 'del','default'])
               subprocess.call(['route', 'add','default','dev', item])
               add_dns(item)
               process = subprocess.Popen(['java', '-jar', '/opt/monroe/NetalyzrCLI.jar'], stdout=subprocess.PIPE)
               result = process.communicate()[0]        
               wr_str = "/tmp/res/mnr-" + nodeid + "_" + item

               try:
                   dnsproc = subprocess.Popen(['cat','/etc/resolv.conf'], stdout=subprocess.PIPE)
                   result_dns = dnsproc.communicate()[0]
               except Exception as e:
                   result_dns = e

               with open(wr_str, 'w') as wr_file:
                   wr_file.write("ID: " + str(nodeid) + "\n")
                   wr_file.write("Interface: " + item +"\n")
                   wr_file.write("Operator: " + str(operator) +"\n")
                   wr_file.write("Resolv.conf:\n" + str(result_dns)+ "\n")

               result_files.append(wr_str)
               with open(wr_str, 'a') as wr_file:
                   wr_file.write(result)
               process = subprocess.Popen(['curl', 'https://stat.ripe.net/data/whats-my-ip/data.json'], stdout=subprocess.PIPE)
               result = process.communicate()[0]        
               with open(wr_str, 'a') as wr_file:
                   wr_file.write(result)
            except Exception as e:
                logger.error(e)   
        
    for result_file in result_files:
        try:
            subprocess.call(['/usr/bin/mv', result_file, '/monroe/results/'])
        except:
            pass
    ip.release()

if __name__ == "__main__":
    sys.exit(main())

