#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date: July 2016
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""Simple util to get a filename/values from defined parameters."""

import psutil


def getname(clientip, clientport, startts, endts):
    return "{}_{}_{}_{}".format(clientip, clientport, startts, endts)


def getvalues(name):
    (clientip, clientport, startts, ending) = name.split('_')
    endts, status = ending.split('.')
    if status != "key":
        raise Exception("No keyfile : {}".format(name))
    return (clientip, clientport, startts, endts)


def get_first_free_port(ip, startport, claimed):
    usedports = []
    for c in psutil.net_connections(kind='inet'):
        if c.status == psutil.CONN_LISTEN:
            addr, port = c.laddr
            if ((addr == ip or ip == "" or ip == "0.0.0.0") and
               port >= startport):
                usedports.append(port)
    for p in range(startport, 65535):
        if p not in usedports and p not in claimed:
            return p
