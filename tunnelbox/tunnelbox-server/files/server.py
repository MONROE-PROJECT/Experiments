#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date: May 2016
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""
Query a specifid url for a list of pubkeys.
"""

from subprocess import check_output
import json

# Configuration
DEBUG = True
CONFIGFILE = './config'

# Default values (overwritable from the scheduler)
# Can only be updated from the main thread and ONLY before any
# other processes are started
EXPCONFIG = {
        "certfile": "CERT.pem",
        "keyfile": "FILE.key",
        "url": "https://scheduler.monroe-system.eu:4443/v1/backend/pubkeys",
        "tunnelserver": "192.168.1.68",
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        }

if __name__ == '__main__':
    """The main thread."""

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

    # Short hand variables and check so we have all variables we need
    try:
        client_cert = EXPCONFIG['certfile']
        client_key = EXPCONFIG['keyfile']
        url = EXPCONFIG['url']
        verbosity = EXPCONFIG['verbosity']
        sslcert = EXPCONFIG['certfile']
    except Exception as e:
        print "Missing expconfig variable {}".format(e)
        raise e

    output = check_output(["curl", "--key", "Downloads/jonas.key", "--cert", "Downloads/jonas.pem", "--insecure", "https://scheduler.monroe-system.eu:4443/v1/backend/pubkeys"])
    # Clean away leading and trailing whitespace
    output = output.strip(' \t\r\n\0')
    for key in json.loads(output)
        print key
