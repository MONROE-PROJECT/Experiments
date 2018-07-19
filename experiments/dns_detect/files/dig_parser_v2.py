#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import sys
#import psycopg2
#from psycopg2.extensions import AsIs

experiment_id = 0
resolver = 0
resolverIP = 0
target = 0
publicIPSubnet = "0.0.0.0"
digversion = 0
startTime = 0
endTime = 0
inputFile = 0
ednsVersion = 0
protocol = 0
overallSize = 0
clientSubnetSupport = False
queryTime = 0
time = 0
messageSize = 0
server = 0
digClientSubnetFlag = "0"
dnsSecSupport = False

'''
dig -b 172.18.21.2 instagramstatic-a.akamaihd.net +cmd

; <<>> DiG 9.10.3-P4-Debian <<>> -b 172.18.21.2 instagramstatic-a.akamaihd.net +noquestion
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 35363
;; flags: qr rd ra; QUERY: 1, ANSWER: 4, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4096
;; ANSWER SECTION:
instagramstatic-a.akamaihd.net. 169 IN  CNAME   instagramstatic-a.akamaihd.net.edgesuite.net.
instagramstatic-a.akamaihd.net.edgesuite.net. 16042 IN CNAME a1168.dsw4.akamai.net.
a1168.dsw4.akamai.net.  19  IN  A   95.101.142.27
a1168.dsw4.akamai.net.  19  IN  A   104.84.152.27

;; Query time: 31 msec
;; SERVER: 195.67.199.18#53(195.67.199.18)
;; WHEN: Fri Nov 17 15:01:44 UTC 2017
;; MSG SIZE  rcvd: 178


'''


"""
rewrite to be able to parse properly the following where the DNS IP have the same line format
as the content server IPs
also try to parse when the flags option has the parameter do
dig -b 172.18.21.2 instagramstatic-a.akamaihd.net +cmd

; <<>> DiG 9.9.5-3ubuntu0.13-Ubuntu <<>> graph.facebook.com
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 56885
;; flags: qr rd ra; QUERY: 1, ANSWER: 3, AUTHORITY: 2, ADDITIONAL: 3

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4096
;; QUESTION SECTION:
;graph.facebook.com.        IN  A

;; ANSWER SECTION:
graph.facebook.com. 475 IN  CNAME   api.facebook.com.
api.facebook.com.   480 IN  CNAME   star.c10r.facebook.com.
star.c10r.facebook.com. 28  IN  A   31.13.68.12

;; AUTHORITY SECTION:
c10r.facebook.com.  3387    IN  NS  b.ns.c10r.facebook.com.
c10r.facebook.com.  3387    IN  NS  a.ns.c10r.facebook.com.

;; ADDITIONAL SECTION:
b.ns.c10r.facebook.com. 399 IN  A   69.171.255.11
b.ns.c10r.facebook.com. 399 IN  AAAA    2a03:2880:ffff:b:face:b00c:0:99

;; Query time: 8 msec
;; SERVER: 127.0.1.1#53(127.0.1.1)
;; WHEN: Tue Feb 28 10:02:07 KST 2017
;; MSG SIZE  rcvd: 184
"""

def parse_dig(dig_output):
    metrics = {}
    answerLine = re.compile(r'(\S+)\s*(\d+)\s*IN\s*(\S+)\s*(\S+)')
    pseudosectionLine = re.compile(r'; EDNS: version: (\d+), flags: ?(\S+)?; (\S+): (\d+)')
    answerSectionHeader = re.compile(r';;\s*ANSWER\s*SECTION:')
    questionSectionHeader = re.compile(r';;\s*QUESTION\s*SECTION:')
    optSectionHeader = re.compile(r';;\s*OPT\s*PSEUDOSECTION:')
    authoritySectionHeader = re.compile(r';;\s*AUTHORITY\s*SECTION:')
    additionalSectionHeader = re.compile(r';;\s*ADDITIONAL\s*SECTION:')

    #metrics["digClientSubnetFlag"] = {"0": False, "1": True}.get(digClientSubnetFlag)
    
    text = dig_output.readlines()
    digResult = "".join([s for s in dig_output.splitlines(True) if s.strip("\r\n")])
    #except:
    #    digResult = dig_output

    #print str(digResult) + "\n"

    line = digResult[1]
    elements = line.split(" ")
    digversion = elements[3].split("-")[0]
    metrics["digversion"] = digversion
    print "DIG version: " + str(digversion)
    for ele in elements[5:]:
        if ele.startswith("@"):
            resolverIP = ele[1:]
            metrics["resolverIP"] = resolverIP
            continue
        if ele.startswith("+subnet="):
            publicIPSubnet = ele[ele.find("=") + 1:].split("/")[0]
            metrics["publicIPSubnet"] = publicIPSubnet
            continue
        if ele.find(".") >= 0:
            target = ele
            #metrics["target"] = target
            continue

    print "Line 7: " + str(digResult[7])
    if digResult[7].find("PSEUDOSECTION") >= 0:
        # the PSEUDOSECTION is present and we parse it
        line = digResult[8]
        (ednsVersion, flags, protocol, overallSize) = pseudosectionLine.search(line).groups()
        if digResult[9].find("CLIENT-SUBNET") >= 0:
            #print("CLIENT-SUBNET")
            clientSubnetSupport = True
            lines = digResult[10:]
            print "DIG results: " + str(lines)
        else:
            #print("NO")
            clientSubnetSupport = False
            lines = digResult[9:]
        try:
            if flags.find("do") >= 0:
                dnsSecSupport = "yes"
            else:
                dnsSecSupport = "no"
        except:
            dnsSecSupport = "error"
    else:
        dnsSecSupport = "N/A"
        (ednsVersion, flags, protocol, overallSize) = (-1, -1, -1, -1)
        clientSubnetSupport = False # if it had there would  be a pseudosection
        lines = digResult[7:]

        metrics["EDNS"] = ednsVersion
        metrics["flags"] = flags
        metrics["protocol"] = protocol
        metrics["acceptedSize"] = overallSize
        metrics["clientSubnetSupport"] = clientSubnetSupport
        metrics["dnsSecSupport"] = dnsSecSupport


    sections = {
        "ans": [],
        "question": [],
        "authority": [],
        "additional": [],
    }

    section = ""
    for line in lines:
        if answerSectionHeader.search(line):
            section = "ans"
        if questionSectionHeader.search(line):
            section = "question"
        if authoritySectionHeader.search(line):
            section = "authority"
        if additionalSectionHeader.search(line):
            section = "additional"
        if line.startswith(";; Query time:"):
            break
        if answerLine.search(line):
            (leftSide, TTL, typeOfRecord, rightSide) = answerLine.search(line).groups()
            sections[section].append(
            {"leftSide": leftSide,
             "TTL": TTL,
             "typeOfRecord": typeOfRecord,
             "rightSide": rightSide
                }
            )
    queryTime = lines[-6].split(" ")[3].strip()
    server = lines[-5].split(" ")[2].strip()
    time = lines[-4][lines[-4].find(": ") + 2:].strip()
    messageSize = lines[-3].split(" ")[-1].strip()

    metrics["queryTime"] = queryTime
    metrics["server"] = server
    metrics["when_human"] = time
    metrics["msgsize"] = messageSize
    metrics["answer"] = sections
    return metrics


if __name__ == '__main__':
    import sys
    import json
    dig_out = open(sys.argv[1], 'r')
    print(json.dumps(parse_dig(dig_out)))




