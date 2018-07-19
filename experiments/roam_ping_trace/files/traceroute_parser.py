#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Leonhard Wimmer
# Date: June 2017
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

import re
from collections import OrderedDict

try:
    from asn_lookup import get_asn
except Exception as e:
    def get_asn(ip):
        return None

HEADER_RE = re.compile(r'^traceroute to (?P<target>\S+?)\s*(?:\((?P<target_ip>\S+)\))?[\s,]+' +
    '(?P<hops_max>\d+)\s+hops max[\s,]+(?P<pkt_size>\d+)\sbyte packets')

HOP_RE = re.compile(r'^\s*(?P<hop>\d+)\s+(?P<probes>.*)$', re.MULTILINE)

PROBE_RE = re.compile(r'(?:(?P<name>[^\s*]+)?\s+)?(?:\(\s*(?P<ip>[^\s]+)\s*\)\s+)?(?:\[(?P<asn>[^\s]+)\]\s+)?(?:(?P<rtt>[\d.]+?)\s+ms(?:\s+(?P<annotation>![^\s]*))?|\s*(?P<star>\*)\s*)')

def parse_traceroute(data, asnlookup=True):
    m = HEADER_RE.match(data)
    if not m:
        return None
    result = OrderedDict()
    result['target'] = m.group('target')
    result['target_ip'] = m.group('target_ip')
    result['hops_max'] = m.group('hops_max')
    result['pkt_size'] = m.group('pkt_size')
    result['hops'] = []
    for m in HOP_RE.finditer(data):
        probes = []
        #print "x"+m.group('probes')+"x"
        name = None
        ip = None
        asn = None
        for p in PROBE_RE.finditer(m.group('probes')):
            #print p.group(0)
            if p.group('name'):
                name = p.group('name')
            if p.group('ip'):
                ip = p.group('ip')
            if p.group('asn'):
                asn = p.group('asn')
                if asn == '*':
                    asn = None
            if asnlookup and ip and not asn:
                asn = get_asn(ip)
                if asn:
                    asn = "AS" + asn
            rtt = p.group('rtt')
            try:
                rtt = float(rtt)
            except Exception as e:
                pass
            probe = OrderedDict()
            probe['name'] = name
            probe['ip'] = ip
            probe['asn'] = asn
            probe['rtt'] = rtt
            probe['annotation'] = p.group('annotation')
            probes.append(probe)
        hop = OrderedDict()
        hop['hop'] = int(m.group('hop'))
        hop['probes'] = probes
        result['hops'].append(hop)
    return result

if __name__ == '__main__':
    import sys
    import json
    data = ""
    for line in sys.stdin:
        data += line
    print(json.dumps(parse_traceroute(data)))
