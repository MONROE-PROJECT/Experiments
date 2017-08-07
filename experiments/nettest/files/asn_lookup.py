#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Leonhard Wimmer
# Date: June 2017
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

import sys
import re
from dns.resolver import Resolver
from IPy import IP

ASN_REGEX = re.compile(r'^(?P<asn>\d+) |')

def get_asn(ip):
    try:
        ipy = IP(ip)
        if ipy.iptype() == 'PRIVATE':
            return None
        host = ipy.reverseName()
        host = host.replace('.in-addr.arpa.', '.origin.asn.cymru.com.')
        host = host.replace('.ip6.arpa.', '.origin6.asn.cymru.com.')
        record = Resolver().query(host, "TXT")
        m = ASN_REGEX.match(record[0].strings[0])
        return m.group('asn')
    except Exception as e:
        #print e
        #raise
        return None


if __name__ == '__main__':
    print(get_asn(sys.argv[1]))
