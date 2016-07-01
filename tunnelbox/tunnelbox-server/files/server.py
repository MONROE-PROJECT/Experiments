#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date: May 2016
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""
Simple web API to enable ssh tunnels on demand.

The script will run forever and listen to correct tokens.
If it get a valid TOTP token it will save the supplied pubkey with temp name.
"""

import time
import BaseHTTPServer
import urlparse
import ssl
import json
import sys
import pyotp
import os
import socket
import subprocess
import tunnel_server_util

# Configuration
DEBUG = True
CONFIGFILE = '/monroe/config'

# Default values (overwritable from the scheduler)
# Can only be updated from the main thread and ONLY before any
# other processes are started
EXPCONFIG = {
        "hostip": "0.0.0.0",
        "webport": 9000,
        "sharedsecret": "INKF26AB345PESNF",
        "certfile": "",
        "sship": "192.168.1.68",
        "sshuser": "user",
        "sshstartport": 10000,
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "validwindow": 0,  # Clock skew to allow ()-validwindow, validwindow+1)
        "resultdir": "/monroe/results/"
        }

CLAIMEDPORTS = []


class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/plain")
        s.end_headers()

    def do_POST(self):
        global CLAIMEDPORTS
        try:
            totp = EXPCONFIG['TOTP']
            window = EXPCONFIG['validwindow']
            outdir = EXPCONFIG['resultdir']
            startport = EXPCONFIG['sshstartport']
            ip = EXPCONFIG['hostip']
            user = EXPCONFIG['sshuser']
            sship = EXPCONFIG['sship']
            hostkey = EXPCONFIG['HOSTKEY']
            length = int(self.headers['Content-Length'])
            (clientip, clientport) = self.client_address
            query = urlparse.parse_qs(self.rfile.read(length).decode('utf-8'),
                                      strict_parsing=True)
            token = int(query["token"][0])
            nodeid = int(query["nodeid"][0])
            guid = str(query["guid"][0])
            pubkey = str(query["pubkey"][0])
            enddate = float(query["enddate"][0])
            now = time.time()
            for i, (ps, ts) in enumerate(CLAIMEDPORTS):
                if now > ts:
                    CLAIMEDPORTS.pop(i)
            currentclaimed = [p for (p, ts) in CLAIMEDPORTS]
            if totp.verify(token, valid_window=window):
                filename = tunnel_server_util.getname(clientip,
                                                      clientport,
                                                      time.time(),
                                                      enddate)
                port = tunnel_server_util.get_first_free_port(ip,
                                                              startport,
                                                              currentclaimed)
                CLAIMEDPORTS.append((port, enddate))
                with open(outdir + filename + ".tmp", 'w') as f:
                    f.write(pubkey)
                    f.flush()
                    os.fsync(f.fileno())

                os.rename(filename + ".tmp", filename + ".key")
                os.chmod(filename + ".key", 0644)

                self.send_response(200)  # 20O: OK
                self.send_header("Content-type", "text/json")
                self.end_headers()
                retur = {
                            'valid': enddate,
                            'port': port,
                            'user': user,
                            'server': sship,
                            'hostkey': hostkey
                        }
                CLAIMEDPORTS.append((port, enddate))
                self.wfile.write(json.dumps(retur,
                                            sort_keys=True,
                                            indent=3))
            else:
                self.send_response(404)  # 404: Unknown error
                print "Failed verification for {}".format(token)
        except Exception as e:
            self.send_response(404)  # 404: Unknown error
            print "Failed at parsing {}".format(e)


if __name__ == '__main__':
    """The main thread control the processes (experiment/metadata)."""

    if not DEBUG:
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
        EXPCONFIG['resultdir'] = "./"

    # Short hand variables and check so we have all variables we need
    try:
        ip = EXPCONFIG['hostip']
        sharedsecret = EXPCONFIG['sharedsecret']
        port = EXPCONFIG['webport']
        verbosity = EXPCONFIG['verbosity']
        outdir = EXPCONFIG['resultdir']
        sslcert = EXPCONFIG['certfile']
        sshserver = EXPCONFIG['sship']
        window = EXPCONFIG['validwindow']
        EXPCONFIG['sshuser']
    except Exception as e:
        print "Missing expconfig variable {}".format(e)
        raise e

    # We now have a updated sharedsecret so lets create the TOTP
    EXPCONFIG['TOTP'] = pyotp.TOTP(EXPCONFIG['sharedsecret'])
    EXPCONFIG['HOSTKEY'] = subprocess.check_output(["ssh-keyscan",
                                                    "-t", "rsa",
                                                    sshserver])
    # Create http server
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((ip, port), MyHandler)
    # httpd.socket = ssl.wrap_socket (httpd.socket, certfile=sslcert'path/to/localhost.pem', server_side=True)

    print time.asctime(), "Server Starts - %s:%s" % (ip, port)
    try:
        # Start the http server
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (ip, port)
