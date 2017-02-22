#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Foivos Michelinakis
# Date: February 2017
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project


"""
Parses the output of a traceroute instance and creates a JSON file compatible with the related table of the MONROE database.
The database schema can be found here:

https://github.com/MONROE-PROJECT/Database/blob/master/db_schema.cql

It then copies the file to the export (results) directory.
"""

import re
import json
import sys
import os
import collections
import itertools
import shutil

IPv4_RE = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
IPv4WithParenthesis_RE = re.compile(r'^\((?:[0-9]{1,3}\.){3}[0-9]{1,3}\)$')
characterExists_re = re.compile(r'([A-Za-z]+)')
float_re = re.compile(r'\d+\.\d+')
int_re = re.compile(r'\d+')
HEADER_RE = re.compile(r'traceroute to (\S+) \((\d+\.\d+\.\d+\.\d+)\), ([0-9]+) hops max, ([0-9]+) byte packets')

CURRENT_DIR = os.getcwd() + "/"
CONFIG_FILE = os.getcwd() + "/intermediate.json"
RESULTS_DIR = "/monroe/results/"
SCRIPT_DIR = '/opt/traceroute/'

with open(CONFIG_FILE, "r") as fd:
    variables = json.load(fd)

usingDefaults = variables["usingDefaults"]  # not inserted in the database
nodeId = variables["nodeId"]
protocolFlag = variables["protocolFlag"]  # not inserted in the database
containerTimestamp = variables["containerTimestamp"]
DataVersion = variables["DataVersion"]
DataId = variables["DataId"]

outputFilename = sys.argv[1]
outputFilenameInfo = outputFilename.split("_")
timestamp = outputFilenameInfo[1]
endTime = outputFilenameInfo[2]
InterfaceName = outputFilenameInfo[3]
protocol = outputFilenameInfo[4]
target = outputFilenameInfo[5][:-4]

#productionJSONName = str(nodeId) + "_" + DataId + "_1_" + str(timestamp) + ".6.parsed"
productionJSONName = str(nodeId) + "_" + DataId + "_1_" + str(timestamp) + "_" + \
                    "_" + target + "_1_" + InterfaceName + "_" + str(endTime) + ".6.parsed"

def addQuotes(toAddQuotes):
    return "\"" + toAddQuotes + "\""


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

boilerplateSection = [
    "targetDomainName", addQuotes(str(target)),
    "NodeId", nodeId,
    "timestamp", timestamp,
    "endTime", endTime,
    "DataId", addQuotes(DataId),
    "InterfaceName", addQuotes(InterfaceName),
    "DataVersion", DataVersion,
    "containerTimestamp", containerTimestamp
    ]

with open(CURRENT_DIR + sys.argv[1], "rb") as inputFile:
    tracerouteResult = inputFile.readlines()

def annotationTextToInteger(annotationTextFormat):
    """
    In the database we can only insert an integer for the field of the annotation.
    The format of the code is 'exclamation mark' + 'capital letter or question mark' + 'number'
    If there is no annotation the number 0 is returned.
    The exclamation mark is symbolised as a leading 1. If it is a single exclamation mark then the number 1 is returned.
    00 (2 zeroes) seperate the annotation characters and indicate that the following code is a letter.
    10 seperate the annotation characters and indicate that the following code is a number.
    Numbers are passed as they are.
    characters are mapped to their ascii codes.
    """
    if annotationTextFormat == 0:
        return 0
    annotationTextFormat.replace(" ", "") # remove all whitespaces
    if annotationTextFormat == "!":
        return 1
    try: # exclamation mark followed directly by a number
        numeric = int(annotationTextFormat[1:])
        return int(str(110) + str(numeric))
    except:
        pass
    # exclamation mark followed by character/ question mark, and optionally followed by number
    letter = ord(annotationTextFormat[1])
    if len(annotationTextFormat) > 2:
        numeric = int(annotationTextFormat[2:])
        return int(str(100) + str(letter) + str(10) + str(numeric))
    else:
        return int(str(100) + str(letter))

def parseSimpleTraceroute(lines):
    while lines[0].startswith("[WARN]"):
        lines.pop(0)

    if (lines[0].find("Name or service not known") >= 0) or (lines[0].find("ERROR") >= 0):
        print "broken traceroute"
        return

    hops = collections.OrderedDict()

    header = lines[0].split()
    if header[0] != "traceroute" or header[1] != "to":
        print "failed to parse header. Header does not have standard format"
        return
    (NameDst, IpDst, numberOfHops, sizeOfProbes) = (header[2], header[3][1:-2], header[4], header[7])
    hops["header"] = (NameDst, IpDst, numberOfHops, sizeOfProbes)
    
    # parse the hop lines
    HopCount = 0
    for line in lines[1:]:
        if len(line) == 0:  # check if the line is empty
            continue
        HopCount += 1
        elements = line.split()
        hopNumber = elements.pop(0)
        hops[hopNumber] = {}
        lastIPFound = ""
        while len(elements) > 0:
            if elements[0] == "*":
                elements.pop(0)
                continue
            elif IPv4_RE.match(elements[0]) or \
            IPv4WithParenthesis_RE.match(elements[0]) or \
            (elements[0].find(":") >= 0) or \
            ((characterExists_re.search(elements[0])) and (elements[0].find(":") < 0)):
                #IPv4 or IPv6 or Name (Human readable)
                if (elements[0].find("(") < 0) and \
                    (elements[1].find("(") >= 0) and \
                    (float_re.match(elements[2]) or int_re.match(elements[2])) and \
                    (elements[3] == "ms"):
                    
                    HopName = elements[0]
                    HopIp = elements[1]
                    lastIPFound = elements[1]
                    HopRTT = int(1000 * float(elements[2])) # The RTT value has to be an interger in order to enter the database, so it is stored as us
                    if len(elements) >= 5 and (not is_number(elements[4])) and elements[4] != "*" and (elements[4].find("!") >= 0):
                        # This probe has an annotation that we have to keep track of
                        annotation = elements[4]
                        if HopIp in hops[hopNumber].keys():# in case an IP appears again eg. when the 1st and 3rd probe have the same IP.
                            hops[hopNumber][HopIp]["HopRTT"].append(HopRTT)
                            hops[hopNumber][HopIp]["annotation"].append(annotation)
                        else:
                            hops[hopNumber][HopIp] = {
                            "HopName": HopName,
                            "HopRTT": [HopRTT],
                            "annotation": [annotation]
                            }
                        elements = elements[5:]
                        continue
                    elements = elements[4:]
                    if HopIp in hops[hopNumber].keys():# in case an IP appears again eg. when the 1st and 3rd probe have the same IP.
                        hops[hopNumber][HopIp]["HopRTT"].append(HopRTT)
                        hops[hopNumber][HopIp]["annotation"].append(0)
                    else:
                        hops[hopNumber][HopIp] = {
                        "HopName": HopName,
                        "HopRTT": [HopRTT],
                        "annotation": [0]
                        }
                else:
                    print "parse failure at hop: %d" % (HopCount)
                    #user_input = raw_input("Some input please: ")
                    break # it breaks the while. If we fail at a hop, we continue at the next one.
            elif (float_re.match(elements[0]) or int_re.match(elements[0])) and \
            (elements[1] == "ms"):
                # probe of the same IP address
                try:
                    if len(elements) >= 3 and (not is_number(elements[2])) and elements[2] != "*" and (elements[2].find("!") >= 0):
                        hops[hopNumber][lastIPFound]["HopRTT"].append(int(1000 * float(elements[0])))
                        hops[hopNumber][lastIPFound]["annotation"].append(elements[2])
                        elements = elements[3:]
                        continue
                    hops[hopNumber][lastIPFound]["HopRTT"].append(int(1000 * float(elements[0])))
                    hops[hopNumber][lastIPFound]["annotation"].append(0)
                    elements = elements[2:]
                except:
                    print "Not able to associate an RTT value with an  IP for hop: %s" % (hopNumber)
                    continue
    return hops

def flattenSimple(toFlatten):
    """
    flatten dict from simple traceroute
    """
    listOfIpHopCombinationDictionaries = []
    header = toFlatten['header']
    if len(header) == 4:
        # header of a normal traceroute
        # In the following line the "NameDst" is removed, since it contains the same information as the field "targetdomainname"
        headerSection = boilerplateSection + ["IpDst", addQuotes(str(header[1])),
                         "numberOfHops", str(header[2]),  "sizeOfProbes", str(header[3])]
    else:
        print "unable to associate header section with a traceroute mode"
        return
    onlyHops = collections.OrderedDict(itertools.islice(toFlatten.iteritems(), 1, None))
    for hopNumber, hopDictionary in onlyHops.iteritems():
        listOfIPsForThisHop = [ip for ip in hopDictionary.keys() if ip.find('.') >= 0] # The only keys in this dict that have dots are the IPs
        for ip in listOfIPsForThisHop:
            IPsection = ["IP", addQuotes(ip[1:-1]),
                        "HopName", addQuotes(hopDictionary[ip]['HopName'])]
            if len(hopDictionary[ip]['HopRTT']) > 0:
                RTTSection = "["
                annotationSection = "["
                for replyNumber in range(len(hopDictionary[ip]['HopRTT'])):
                    RTTSection += str(hopDictionary[ip]['HopRTT'][replyNumber]) + ", "
                    annotationSection += str(annotationTextToInteger(hopDictionary[ip]['annotation'][replyNumber])) + ", "
                RTTSection = RTTSection[:-2] + "]"
                annotationSection = annotationSection[:-2] + "]"
            else:
                RTTSection = ""
                annotationSection = ""
            allSections = ["hop", hopNumber] + headerSection + IPsection + ["RTTSection", RTTSection] + ["annotationSection", annotationSection]
            ipHopEntry = collections.OrderedDict()
            for i in range(0, len(allSections), 2):
                ipHopEntry[allSections[i]] =  allSections[i+1]
            listOfIpHopCombinationDictionaries.append(ipHopEntry)           
        if len(listOfIPsForThisHop) == 0:
            allSections = ["hop", hopNumber] + headerSection + ["IP", addQuotes("Fail")]
            ipHopEntry = collections.OrderedDict()
            for i in range(0, len(allSections), 2):
                ipHopEntry[allSections[i]] =  allSections[i+1]
            listOfIpHopCombinationDictionaries.append(ipHopEntry)
    return listOfIpHopCombinationDictionaries


def exportToDatabase(dictionaryToParse, productionJSONName):
    DatabaseEntries = """"""
    for element in dictionaryToParse:
        DatabaseEntry = "{"
        for key, value in element.iteritems():
            DatabaseEntry += ("\"" + str(key) + "\": " + str(value) + ", ")
        DatabaseEntry = DatabaseEntry[:-2] + "}\n"
        DatabaseEntries += DatabaseEntry
    with open(CURRENT_DIR + productionJSONName, "w") as outputFile:
        outputFile.write(DatabaseEntries)
    # we copy the results to the RESULTS_DIR, so that they can be
    # send to the database. We do not copy directly the files in order
    # to avoid possible corruption during the automatic export.
    shutil.copy2(CURRENT_DIR + productionJSONName, RESULTS_DIR + productionJSONName + ".tmp")
    shutil.move(RESULTS_DIR + productionJSONName + ".tmp", RESULTS_DIR + productionJSONName.replace(".parsed", ".json"))


hops = flattenSimple(parseSimpleTraceroute(tracerouteResult))
exportToDatabase(hops, productionJSONName)