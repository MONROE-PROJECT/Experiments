#!/usr/bin/python
import sys
import re
import pprint
import collections
import os
import pdb
import json
import itertools
import argparse
import zmq


traceroute_annotations = {
"!" : "ttl <= 1",
"!H" : "host unreachable",
"!N" : "network unreachable",
"!P" : "protocol unreachable",
"!S" : "source route failed",
"!U" : "destination network/host unknown",
"!W" : "destination network/host unknown",
"!I" : "source host is isolated",
"!A" : "communication with destination network administratively prohibited",
"!Z" : "communication with destination host administratively prohibited",
"!Q" : "for this ToS the destination network is unreachable",
"!T" : "for this ToS the destination host is unreachable",
"!X" : "communication administratively prohibited",
"!V" : "host precedence violation",
"!C" : "precedence cutoff in effect",
"!0" : "ICMP destination unreachable code 0: Network unreachable error.",
"!1" : "ICMP destination unreachable code 1: Host unreachable error.",
"!2" : "ICMP destination unreachable code 2: Protocol unreachable error (the designated transport protocol is not supported).",
"!3" : "ICMP destination unreachable code 3: Port unreachable error (the designated protocol is unable to inform the host of the incoming message).",
"!4" : "ICMP destination unreachable code 4: The datagram is too big. Packet fragmentation is required but the 'don't fragment' (DF) flag is on.",
"!5" : "ICMP destination unreachable code 5: Source route failed error.",
"!6" : "ICMP destination unreachable code 6: Destination network unknown error.",
"!7" : "ICMP destination unreachable code 7: Destination host unknown error.",
"!8" : "ICMP destination unreachable code 8: Source host isolated error.",
"!9" : "ICMP destination unreachable code 9: The destination network is administratively prohibited.",
"!10" : "ICMP destination unreachable code 10: The destination host is administratively prohibited.",
"!11" : "ICMP destination unreachable code 11: The network is unreachable for Type Of Service.",
"!12" : "ICMP destination unreachable code 12: The host is unreachable for Type Of Service.",
"!13" : "ICMP destination unreachable code 13: Communication administratively prohibited (administrative filtering prevents packet from being forwarded).",
"!14" : "ICMP destination unreachable code 14: Host precedence violation (indicates the requested precedence is not permitted for the combination of host or network and port).",
"!15" : "ICMP destination unreachable code 15: Precedence cutoff in effect (precedence of datagram is below the level set by the network administrators)."
#"*" : "No response"
}



paristraceroute_annotations = {
"!Q" : "SOURCE_QUENCH",
"!? " : "Default Error",
}

# regular expressions
HEADER_RE = re.compile(r'traceroute to (\S+) \((\d+\.\d+\.\d+\.\d+)\), ([0-9]+) hops max, ([0-9]+) byte packets')
ParisHeader_RE = re.compile(r'traceroute \[\((\d+\.\d+\.\d+\.\d+)\:(\d+)\) \-\> \((\d+\.\d+\.\d+\.\d+)\:(\d+)\)\], protocol ([A-Za-z]+), algo ([A-Za-z]+), duration (\d+) s')
IPv4_RE = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
IPv4WithParenthesis_RE = re.compile(r'^\((?:[0-9]{1,3}\.){3}[0-9]{1,3}\)$')
float_re = re.compile(r'\d+\.\d+')
int_re = re.compile(r'\d+')
characterExists_re = re.compile(r'([A-Za-z]+)')
wrongTtlParisTraceroute_re = re.compile(r'\!T(\d+)')


# parsing command line parameters
parser = argparse.ArgumentParser()
parser.add_argument("-s", "--startTime", default=0,
                     help="The second value of the timestamp right before the traceroute",
                     type=int)
parser.add_argument("-e", "--endTime", default=0,
                     help="The second value of the timestamp right after the traceroute",
                     type=int)
parser.add_argument("-m", "--tracerouteMode", default="N/A",
                     help="The type of traceroute that generated the txt file",
                     type=str, choices = ["simple_traceroute", "paris_traceroute_simple", "paris_traceroute_exhaustive"])
parser.add_argument("-f", "--fileToParse", default="N/A",
                     help="The txt file that is served as the output of the traceroute commands",
                     type=str)
parser.add_argument("-j", "--JsonTracetouteSwitch", default="traceroute",
                     help="Whether to parse a traceroute output (\"traceroute\") or to parse a json file (\"Json\")",
                     type=str, choices = ["traceroute", "Json"])
parser.add_argument("-S", "--productionTestingSwitch", default="testing",
                     help="Whether this code is being run on a MONROE node (\"production\") or on another machine for testing (\"testing\")",
                     type=str, choices = ["production", "testing"])
parser.add_argument("-I", "--InterfaceName", default="usb0",
                     help="The internal (inside the container / network namespace) name of the interfaace used to generate the traceroute output file",
                     type=str, choices = ["op0", "op1", "op2"])
parser.add_argument("-v", "--versionOfParisTraceroute", default="modified",
                     help="Whether we use the modified version of paris-traceroute suitable for use inside the MONROE containers, or the default one that is distributed by the ubuntu/debian repositories",
                     type=str, choices = ["modified", "repository"])
parser.add_argument("-D", "--targetDomainName", default="N/A",
                     help="The domain name of the target of the traceroute",
                     type=str)
args = parser.parse_args()


def addQuotes(toAddQuotes):
    return "\"" + toAddQuotes + "\""

def getMetaData(InterfaceName):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect ("tcp://172.17.0.1:5556")

    topicfilter = "MONROE.META.DEVICE.MODEM"
    socket.setsockopt(zmq.SUBSCRIBE, topicfilter)

    while True:
        string = socket.recv()
        metaData = json.loads(string[string.find("{"):])
        if "InternalInterface" in metaData.keys():
            if metaData["InternalInterface"] == InterfaceName:
                break
    mobileOperator = metaData["Operator"]
    CarrierInternalIP = metaData["IPAddress"]
    DeviceMode = metaData["DeviceMode"]
    DeviceState = metaData["DeviceState"]
    return (mobileOperator, CarrierInternalIP, DeviceMode, DeviceState)


if args.productionTestingSwitch == "production":
    DataVersion = 1
    DataId = {"simple_traceroute": "MONROE.EXP.SIMPLE.TRACEROUTE", "paris_traceroute_simple": "MONROE.EXP.SIMPLE.PARIS", "paris_traceroute_exhaustive": "MONROE.EXP.EXHAUSTIVE.PARIS"}.get(args.tracerouteMode)
    NodeId = 0
    with open("/monroe/config", "r") as fd:
        configurationParameters = json.load(fd)
        NodeId = int(configurationParameters["nodeid"])
    startTime = args.startTime
    endTime = args.endTime
    InterfaceName = args.InterfaceName
    (mobileOperator, CarrierInternalIP, DeviceMode, DeviceState) = getMetaData(InterfaceName)
    boilerplateSection = (
    "targetDomainName", addQuotes(str(args.targetDomainName)),
    "NodeId", NodeId,
    "startTime", args.startTime,
    "endTime", args.endTime,
    "DataId", addQuotes(DataId),
    "InterfaceName", addQuotes(InterfaceName),
    "DataVersion", DataVersion,
    "mobileOperator", addQuotes(mobileOperator),
    "CarrierInternalIP",  addQuotes(CarrierInternalIP),
    "DeviceMode", DeviceMode,
    "DeviceState", DeviceState)
elif  args.productionTestingSwitch == "testing":
    boilerplateSection = ()
else:
    print "The productionTestingSwitch is not properly set. Exiting........."
    sys.exit(1)




def parseSimpleTraceroute(lines, mode):
    """
    simple traceroute (either from the traceroute command or a paris-traceroute without any flags)
    """
    while lines[0].startswith("[WARN]"):
        lines.pop(0)

    if (lines[0].find("Name or service not known") >= 0) or (lines[0].find("ERROR") >= 0):
        print "broken traceroute"
        return

    hops = collections.OrderedDict()

    # parse header

    # parsedHeader = HEADER_RE.match(lines[0])
    # if parsedHeader == None:
    #     print "failed to parse header"
    #     return
    # (NameDst, IpDst, numberOfHops, sizeOfProbes) = parsedHeader.groups()
    # print (NameDst, IpDst, numberOfHops, sizeOfProbes)

    if mode == "simple_traceroute":
        header = lines[0].split()
        if header[0] != "traceroute" or header[1] != "to":
            print "failed to parse header. Header does not have standard format"
            return
        (NameDst, IpDst, numberOfHops, sizeOfProbes) = (header[2], header[3][1:-2], header[4], header[7])
        hops["header"] = (NameDst, IpDst, numberOfHops, sizeOfProbes)
    elif mode == "paris_traceroute_simple":
        header = lines[0].split()
        if header[0] != "traceroute" or header[2] != "->":
            print "failed to parse header. Header does not have standard format"
            return

        parsedHeader = ParisHeader_RE.match(lines[0])
        if parsedHeader == None:
            print "failed to parse header"
            return
        
        (IpSrc, PortSrc, IpDst, PortDst, Proto, Algorithm, duration) = parsedHeader.groups()
        hops["header"] = (IpSrc, PortSrc, IpDst, PortDst, Proto, Algorithm, duration)
    
    # parse the hop lines
    HopCount = 0
    for line in lines[1:]:
        if len(line) == 0:#check if the line is empty
            continue
        # first check if the previous hop has any MPLS related data
        if (mode == "paris_traceroute_simple") and (line.startswith("   MPLS Label ")):
            keyOfLastElement = next(reversed(hops))
            if int_re.match(str(keyOfLastElement)) == None:# if the key of the last hop is not an integer something is wrong
                print "Unable to associate MPLS header with a hop"
                return
            else:
                hops[keyOfLastElement]["MPLS"] = line.strip()
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
                    HopRTT = float(elements[2])
                    if len(elements) >= 5:
                        if (mode == "paris_traceroute_simple") and (elements[4] in paristraceroute_annotations.keys()):
                            # This probe has an annotation that we have to keep track of
                            annotation = elements[4]
                            if HopIp in hops[hopNumber].keys():# in case an IP appears again eg. when the 1st and 3rd probe have the same IP.
                                hops[hopNumber][HopIp]["HopRTT"].append(HopRTT)
                                hops[hopNumber][HopIp]["annotation"].append(annotation)
                                hops[hopNumber][HopIp]["annotationExplanation"].append(paristraceroute_annotations[elements[4]])
                            else:
                                hops[hopNumber][HopIp] = {
                                "HopName": HopName,
                                "HopRTT": [HopRTT],
                                "annotation": [annotation],
                                "annotationExplanation": [paristraceroute_annotations[elements[4]]]
                                }
                            elements = elements[5:]
                            continue
                        if (mode == "paris_traceroute_simple") and (wrongTtlParisTraceroute_re.match(elements[4]) != None):
                            # This probe has an annotation that we have to keep track of
                            annotation = elements[4]
                            if HopIp in hops[hopNumber].keys():# in case an IP appears again eg. when the 1st and 3rd probe have the same IP.
                                hops[hopNumber][HopIp]["HopRTT"].append(HopRTT)
                                hops[hopNumber][HopIp]["annotation"].append(annotation)
                                hops[hopNumber][HopIp]["annotationExplanation"].append("the TTL of the reply is %s" % (elements[4][2:]))
                            else:
                                hops[hopNumber][HopIp] = {
                                "HopName": HopName,
                                "HopRTT": [HopRTT],
                                "annotation": [annotation],
                                "annotationExplanation": ["the TTL of the reply is %s" % (elements[4][2:])]
                                }
                            elements = elements[5:]
                            continue
                        if elements[4] in traceroute_annotations.keys():
                            # This probe has an annotation that we have to keep track of
                            annotation = elements[4]
                            if HopIp in hops[hopNumber].keys():# in case an IP appears again eg. when the 1st and 3rd probe have the same IP.
                                hops[hopNumber][HopIp]["HopRTT"].append(HopRTT)
                                hops[hopNumber][HopIp]["annotation"].append(annotation)
                                hops[hopNumber][HopIp]["annotationExplanation"].append(traceroute_annotations[elements[4]])
                            else:
                                hops[hopNumber][HopIp] = {
                                "HopName": HopName,
                                "HopRTT": [HopRTT],
                                "annotation": [annotation],
                                "annotationExplanation": [traceroute_annotations[elements[4]]]
                                }
                            elements = elements[5:]
                            continue
                    elements = elements[4:]
                    if HopIp in hops[hopNumber].keys():# in case an IP appears again eg. when the 1st and 3rd probe have the same IP.
                        hops[hopNumber][HopIp]["HopRTT"].append(HopRTT)
                        hops[hopNumber][HopIp]["annotation"].append("N/A")
                        hops[hopNumber][HopIp]["annotationExplanation"].append("N/A")
                    else:
                        hops[hopNumber][HopIp] = {
                        "HopName": HopName,
                        "HopRTT": [HopRTT],
                        "annotation": ["N/A"],
                        "annotationExplanation": ["N/A"]
                        }
                else:
                    print "parse failure at hop: %d" % (HopCount)
                    user_input = raw_input("Some input please: ")
                    break # it breaks the while. If we fail at a hop, we continue at the next one.
            elif (float_re.match(elements[0]) or int_re.match(elements[0])) and \
            (elements[1] == "ms"):
                # probe of the same IP address
                try:
                    if len(elements) >= 3:
                        if (mode == "paris_traceroute_simple") and (elements[2] in paristraceroute_annotations.keys()):
                            hops[hopNumber][lastIPFound]["HopRTT"].append(float(elements[0]))
                            hops[hopNumber][lastIPFound]["annotation"].append(elements[2])
                            hops[hopNumber][lastIPFound]["annotationExplanation"].append(paristraceroute_annotations[elements[2]])
                            elements = elements[3:]
                            continue
                        if (mode == "paris_traceroute_simple") and (wrongTtlParisTraceroute_re.match(elements[2]) != None):
                            hops[hopNumber][lastIPFound]["HopRTT"].append(float(elements[0]))
                            hops[hopNumber][lastIPFound]["annotation"].append(elements[2])
                            hops[hopNumber][lastIPFound]["annotationExplanation"].append("the TTL of the reply is %s" % (elements[2][2:]))
                            elements = elements[3:]
                            continue
                        if elements[2] in traceroute_annotations.keys():
                            hops[hopNumber][lastIPFound]["HopRTT"].append(float(elements[0]))
                            hops[hopNumber][lastIPFound]["annotation"].append(elements[2])
                            hops[hopNumber][lastIPFound]["annotationExplanation"].append(traceroute_annotations[elements[2]])
                            elements = elements[3:]
                            continue
                    hops[hopNumber][lastIPFound]["HopRTT"].append(float(elements[0]))
                    hops[hopNumber][lastIPFound]["annotation"].append("N/A")
                    hops[hopNumber][lastIPFound]["annotationExplanation"].append("N/A")
                    elements = elements[2:]
                except:
                    print "Not able to associate an RTT value with an  IP for hop: %s" % (hopNumber)
                    continue
    return hops

def flattenSimple(toFlatten):
    """
    flatten dict from simple traceroute (either paris or normal)
    """
    listOfIpHopCombinationDictionaries = []
    header = toFlatten['header']
    if len(header) == 4:
        # header of a normal traceroute
        headerSection = boilerplateSection + ("NameDst", addQuotes(str(header[0])), "IpDst", addQuotes(str(header[1])),
                         "numberOfHops", str(header[2]),  "sizeOfProbes", str(header[3]))
    elif len(header) == 7:
        # header of a simple paris traceroute
        headerSection = boilerplateSection + ("IpSrc", addQuotes(str(header[0])), "PortSrc", str(header[1]),
                         "IpDst", addQuotes(str(header[2])),  "PortDst", str(header[3]),
                         "Proto", addQuotes(str(header[4])),  "Algorithm", addQuotes(str(header[5])),
                         "duration", str(header[6]))
    else:
        print "unable to associate header section with a traceroute mode"
        return
    onlyHops = collections.OrderedDict(itertools.islice(toFlatten.iteritems(), 1, None))
    for hopNumber, hopDictionary in onlyHops.iteritems():
        listOfIPsForThisHop = [ip for ip in hopDictionary.keys() if ip.find('.') >= 0] # The only keys in this dict that have dots are the IPs
        for ip in listOfIPsForThisHop:
            IPsection = ("IP", addQuotes(ip[1:-1]),
                         "HopName", addQuotes(hopDictionary[ip]['HopName']))
            for replyNumber in range(len(hopDictionary[ip]['HopRTT'])):
                replyProbesSection = ("HopRTT", hopDictionary[ip]['HopRTT'][replyNumber],
                                     "annotation", addQuotes(hopDictionary[ip]['annotation'][replyNumber]), 
                                     "annotationExplanation", addQuotes(hopDictionary[ip]['annotationExplanation'][replyNumber]))
                allSections = ("hop", hopNumber) + headerSection + IPsection + replyProbesSection
                ipHopEntry = collections.OrderedDict()
                for i in range(0, len(allSections), 2):
                    ipHopEntry[allSections[i]] =  allSections[i+1]
                listOfIpHopCombinationDictionaries.append(ipHopEntry)            
        if len(listOfIPsForThisHop) == 0:
            allSections = ("hop", hopNumber) + headerSection + ("IP", "Fail")
            ipHopEntry = collections.OrderedDict()
            for i in range(0, len(allSections), 2):
                ipHopEntry[allSections[i]] =  allSections[i+1]
            listOfIpHopCombinationDictionaries.append(ipHopEntry)
    return listOfIpHopCombinationDictionaries



def parseParisTracerouteExhaustive(lines):
    """
    paris-traceroute exhaustive
    There seems to be no IPv6 support for paris-traceroute. So we ignore the IPv6 case.
    Also it seems to not work when using human readable names for the hopes, so we only parse numerical addresses.
    """
    while lines[0].startswith("[WARN]") or lines[0].startswith("# Bandwidth, sent ="):
        lines.pop(0)

    if (lines[0].find("Name or service not known") >= 0) or (lines[0].find("ERROR") >= 0):
        print "broken traceroute"
        return

    hops = collections.OrderedDict()

    header = lines[0].split()
    if header[0] != "traceroute" or header[2] != "->":
        print "failed to parse header. Header does not have standard format"
        return

    parsedHeader = ParisHeader_RE.match(lines[0])
    if parsedHeader == None:
        print "failed to parse header"
        return
    
    (IpSrc, PortSrc, IpDst, PortDst, Proto, Algorithm, duration) = parsedHeader.groups()
    hops["header"] = (IpSrc, PortSrc, IpDst, PortDst, Proto, Algorithm, duration)

    # parse the hop lines
    HopCount = 0
    for line in lines[1:]:
        # first check if the previous hop has any MPLS related data
        if line.startswith("   MPLS Label "):
            keyOfLastElement = next(reversed(hops))
            if int_re.match(str(keyOfLastElement)) == None:# if the key of the last hop is not an integer something is wrong
                print "Unable to associate MPLS header with a hop"
                return
            else:
                hops[keyOfLastElement]["MPLS"] = line.strip()
                continue
        
        if (len(line) == 0) or (line.find("P(") < 0):#check if the line is empty or does not follow the standard format in general
            continue

        HopCount += 1
        elements = line.split()
        hopNumber = elements.pop(0)
        hops[hopNumber] = {}
        hops[hopNumber]["successfulProbes"] = elements.pop(0)[2:-1]
        hops[hopNumber]["TransmittedProbes"] = elements.pop(0)[:-1]

        if hops[hopNumber]["successfulProbes"] == '0':#All the probes were lost at this hop
            continue
        
        while len(elements) > 0:
            if elements[0].find(":") >= 0:#multiple nodes detected in this hop
                IP = elements[0][:elements[0].find(":")]
                hops[hopNumber][IP] = {
                "flowIds": [int(x) for x in elements[0][elements[0].find(":") + 1:].split(",")]
                }
            else:
                IP = elements[0]
                hops[hopNumber][IP] = {
                "flowIds": "N/A"
                }
            if args.versionOfParisTraceroute == "modified":
                (hops[hopNumber][IP]["MinHopRTT"], hops[hopNumber][IP]["MedianHopRTT"], hops[hopNumber][IP]["MaxHopRTT"], hops[hopNumber][IP]["StdHopRTT"]) = (float(RTTelement) for RTTelement in elements[1].split("/"))
            elif args.versionOfParisTraceroute == "repository":
                hops[hopNumber][IP]["HopRTT"] = float(elements[1])
            if len(elements) > 3:
                if elements[3].find("!") >= 0:# There is an annotation for that hop
                    # each IP has exaclty one RTTT and annotation value in the exhaustive mode
                    if elements[3] in paristraceroute_annotations.keys():
                        hops[hopNumber][IP]["annotation"] = elements[3]
                        hops[hopNumber][IP]["annotationExplanation"] = paristraceroute_annotations[elements[3]]
                    if wrongTtlParisTraceroute_re.match(elements[3]) != None:
                        hops[hopNumber][IP]["annotation"] = elements[3]
                        hops[hopNumber][IP]["annotationExplanation"] = "the TTL of the reply is %s" % (elements[3][2:])
                    if elements[3] in traceroute_annotations.keys():
                        hops[hopNumber][IP]["annotation"] = elements[3]
                        hops[hopNumber][IP]["annotationExplanation"] = traceroute_annotations[elements[3]]
                    elements = elements[4:]
                    continue
            hops[hopNumber][IP]["annotation"] = "N/A"
            hops[hopNumber][IP]["annotationExplanation"] = "N/A"
            elements = elements[3:]
    return hops

def flattenExhaustive(toFlatten):
    """
    flatten dict from exhaustive paris traceroute
    """
    listOfIpHopCombinationDictionaries = []
    header = toFlatten['header']
    headerSection = boilerplateSection + ("IpSrc", addQuotes(str(header[0])), "PortSrc", str(header[1]),
                     "IpDst", addQuotes(str(header[2])),  "PortDst", str(header[3]),
                     "Proto", addQuotes(str(header[4])),  "Algorithm", addQuotes(str(header[5])),
                     "duration", str(header[6]))
    onlyHops = collections.OrderedDict(itertools.islice(toFlatten.iteritems(), 1, None))
    for hopNumber, hopDictionary in onlyHops.iteritems():
        #print hopNumber, hopDictionary
        probeSection  = ('TransmittedProbes', hopDictionary['TransmittedProbes'], 'successfulProbes', hopDictionary['successfulProbes'] )
        if "MPLS" in hopDictionary.keys():
            MPLSSection = ("MPLS", addQuotes(hopDictionary['MPLS']))
        else:
            MPLSSection = ("MPLS", addQuotes(""))
        listOfIPsForThisHop = [ip for ip in hopDictionary.keys() if ip.find('.') >= 0] # The only keys in this dict that have dots are the IPs
        for ip in listOfIPsForThisHop:
            if args.versionOfParisTraceroute == "modified":
                IPsection = ("IP", addQuotes(ip),
                            'MinHopRTT', hopDictionary[ip]['MinHopRTT'],
                            'MedianHopRTT', hopDictionary[ip]['MedianHopRTT'],
                            'MaxHopRTT', hopDictionary[ip]['MaxHopRTT'],
                            'StdHopRTT', hopDictionary[ip]['StdHopRTT'],
                            'annotation', addQuotes(hopDictionary[ip]['annotation']),
                            'annotationExplanation', addQuotes(hopDictionary[ip]['annotationExplanation']),
                            'flowIds', hopDictionary[ip]['flowIds'])
            elif args.versionOfParisTraceroute == "repository":
                IPsection = ("IP", addQuotes(ip),
                            'HopRTT', hopDictionary[ip]['HopRTT'],
                            'annotation', addQuotes(hopDictionary[ip]['annotation']),
                            'annotationExplanation', addQuotes(hopDictionary[ip]['annotationExplanation']),
                            'flowIds', hopDictionary[ip]['flowIds'])
            # for every ip / hop combination we create a dictionary and put it in a list, which will be used to generate the json
            allSections = ("hop", hopNumber) + headerSection + IPsection + MPLSSection
            ipHopEntry = collections.OrderedDict()
            for i in range(0, len(allSections), 2):
                ipHopEntry[allSections[i]] =  allSections[i+1]
            listOfIpHopCombinationDictionaries.append(ipHopEntry)
        if len(listOfIPsForThisHop) == 0:
            allSections = ("hop", hopNumber) + headerSection + ("IP", "Fail") + MPLSSection
            ipHopEntry = collections.OrderedDict()
            for i in range(0, len(allSections), 2):
                ipHopEntry[allSections[i]] =  allSections[i+1]
            listOfIpHopCombinationDictionaries.append(ipHopEntry)
    return listOfIpHopCombinationDictionaries

def printResults(toPrint):
    if toPrint == None:
        print "Failed to parse file"
    else:
        if isinstance(toPrint, dict) or isinstance(toPrint, collections.OrderedDict):
            for key, value in toPrint.iteritems():
                print key, value
        elif isinstance(toPrint, list):
            for element in toPrint:
                print element
        else:
            print "unable to verify the instance of the object to print"


def exportToDatabase(dictionaryToParse, fileToParse, productionJSONName):
    DatabaseEntries = """"""
    for element in dictionaryToParse:
        DatabaseEntry = "["
        for key, value in element.iteritems():
            DatabaseEntry += ("\"" + str(key) + "\": " + str(value) + ", ")
        DatabaseEntry = DatabaseEntry[:-2] + "]\n"
        DatabaseEntries += DatabaseEntry
    if productionJSONName == None:
        with open(fileToParse[:-3] + "json", "w") as fd:
            fd.write(DatabaseEntries)
    else:
        with open(productionJSONName, "w") as fd:
            fd.write(DatabaseEntries)

def mainLogic(fileToParse, tracerouteMode):
    productionJSONName = None
    if args.productionTestingSwitch == "production":
        productionJSONName = str(NodeId) + "_" + DataId + "_1_" + str(startTime) + ".6.json"
    with open(fileToParse, "r") as fd:
        lines = fd.readlines()
        if tracerouteMode in  ["simple_traceroute", "paris_traceroute_simple"]:
            hops = flattenSimple(parseSimpleTraceroute(lines, tracerouteMode))
            printResults(hops)
            exportToDatabase(hops, fileToParse, productionJSONName)
        elif tracerouteMode == "paris_traceroute_exhaustive":
            hops = flattenExhaustive(parseParisTracerouteExhaustive(lines)) # we flatten the dictionary before we pass it to the json exporter, in order to be easilt parsable by the database.
            printResults(hops)
            exportToDatabase(hops, fileToParse, productionJSONName)
        else:
            print "The traceroute mode is wrong. The mode given is: %s" % (tracerouteMode) 
            sys.exit(1)


def JsonParser(fileToParse):
    jsonPrefixUrl = "http://netalyzr.icsi.berkeley.edu/json/id="
    usefulKeys = ["params", "args", "tests"]
    with open(fileToParse, 'rb') as fp:
        parsedFile = json.load(fp)

def JsonDumper(toDump, jsonName):
    if toDump == None:
        print "Failed to parse file"
    else:
        with open(jsonName.replace(".txt", ".json"), 'w') as outfile:
            json.dump(toDump, outfile)

def dictionaryFlattener(toFlat):
    flattened = collections.OrderedDict()
    return flattened


if __name__ == '__main__':
    fileToParse = args.fileToParse
    tracerouteMode = args.tracerouteMode
    JsonTracetouteSwitch = args.JsonTracetouteSwitch
    if JsonTracetouteSwitch == "traceroute":
        mainLogic(fileToParse, tracerouteMode)
    if JsonTracetouteSwitch == "Json":
        JsonParser(fileToParse)
    
if __name__ == "trace":
    for element in [x for x in os.listdir(".") if x.endswith("txt")]:
        if element.lower().find("paris") >= 0:
            print element
            print "paris_traceroute_simple"
            mainLogic(element, "paris_traceroute_simple")
            print "##################################"
            print ""
        elif (element.lower().find("exhaustive") >= 0):
            print element
            print "paris_traceroute_exhaustive"
            mainLogic(element, "paris_traceroute_exhaustive")
            print "##################################"
            print ""
        else:
            print element
            print "simple_traceroute"
            mainLogic(element, "simple_traceroute")
            print "##################################"
            print ""