#!/usr/bin/env python3

# Author: Mohammad Rajiullah <mohammad.rajiullah@kau.se>
# Date: November 2019
# License:

import utime
import uselect
import uctypes
import usocket
import ustruct
import machine
from network import LTE
import time
import usocket
import json

def pprint(msg):
    print(msg, end = '')

def send_at_cmd_pretty(cmd,lte):
    """Prettify AT command output"""
    response = lte.send_at_cmd(cmd).split('\r\n')
    for line in response:
        print(line)

def set_dns(servers=['8.8.8.8','4.4.4.4']):
    """Setting dns for the NB setting"""
    i=0
    for server in servers:
        usocket.dnsserver(i,server)
        i+=1
    pprint(usocket.dnsserver())

def set_nbiot(apn="lpwa.telia.iot", band=None, type=LTE.IP, wait=10):
    """Setting the NB-IOT connection"""
    factor=0.25
    ipdown = True
    lte = LTE()
    lte.reset()
    lte.attach(apn=apn,band=band, type=type)
    i=0
    while not lte.isattached() and i < wait/factor:
        time.sleep(factor)
        i+=1
    if lte.isattached():
        print("Attached to a LTE network (took {} s)".format(i*factor))
        send_at_cmd_pretty('AT+CGCONTRDP',lte)
        lte.connect()       # start a data session and obtain an IP address
    i=0
    while lte.isattached() and not lte.isconnected() and i < wait/factor:
        time.sleep(factor)
        i+=1
    if lte.isconnected():
        print("Connected to a LTE network (took {} s)".format(i*factor))
        i=0
        while ipdown and i < wait/factor:
            ipdown = False
            try:
                usocket.getaddrinfo("8.8.8.8", 80)
            except Exception as e:
                ipdown = True
            time.sleep(factor)
            i+=1
    if not ipdown:
        print("Interface up (took {} s)".format(i*factor))
        pprint("OK")
    else:
        pprint("Failed")

def get_connection_status():
    """Getting NB-IOT connection status"""
    lte = LTE()
    if not lte.isattached():
        pprint("Not attached")
    elif not lte.isconnected():
        pprint("Not connected")
    else:
        try:
            usocket.getaddrinfo("8.8.8.8", 80)
        except Exception as e:
            pprint("Interface down")
        pprint("Connected")

def get_iccid(wait=10):
    factor=0.25
    lte = LTE()
    if lte.isconnected():
        lte.pppsuspend()
        pprint(lte.iccid())
        lte.pppresume()
    else:
        i=0
        while not lte.iccid() and i < wait/factor:
            time.sleep(factor)
            i+=1
        pprint(lte.iccid())

def checksum(data):
    if len(data) & 0x1: # Odd number of bytes
        data += b'\0'
    cs = 0
    for pos in range(0, len(data), 2):
        b1 = data[pos]
        b2 = data[pos + 1]
        cs += (b1 << 8) + b2
    while cs >= 0x10000:
        cs = (cs & 0xffff) + (cs >> 16)
    cs = ~cs & 0xffff
    return cs

def ping(host, count=4, timeout=5000, interval=10, quiet=True, size=64):
    """Ping implementation for upython"""
    assert size >= 16, "pkt size too small"
    pkt = b'Q'*size
    pkt_desc = {
        "type": uctypes.UINT8 | 0,
        "code": uctypes.UINT8 | 1,
        "checksum": uctypes.UINT16 | 2,
        "id": uctypes.UINT16 | 4,
        "seq": uctypes.INT16 | 6,
        "timestamp": uctypes.UINT64 | 8,
    } # packet header descriptor
    h = uctypes.struct(uctypes.addressof(pkt), pkt_desc, uctypes.BIG_ENDIAN)
    h.type = 8 # ICMP_ECHO_REQUEST
    h.code = 0
    h.checksum = 0
    #h.id = urandom.randint(0, 65535)
    h.id = machine.rng() & 0xffff
    h.seq = 1

    # init socket
    #sock = usocket.socket(usocket.AF_INET, usocket.SOCK_RAW, 1)
    sock = usocket.socket(usocket.AF_INET, 3, 1)
    sock.setblocking(0)
    sock.settimeout(timeout/1000)
    addr = usocket.getaddrinfo(host, 1)[0][-1][0] # ip address
    sock.connect((addr, 1))
    not quiet and pprint("PING %s (%s): %u data bytes" % (host, addr, len(pkt)))

    seqs = list(range(1, count+1)) # [1,2,...,count]
    ping_results=[]
    c = 1
    t = 0
    n_trans = 0
    n_recv = 0
    finish = False
    results = []
    while t < timeout:
        if t==interval and c<=count:
            # send packet
            h.checksum = 0
            h.seq = c
            h.timestamp = utime.ticks_us()
            h.checksum = checksum(pkt)
            if sock.send(pkt) == size:
                n_trans += 1
                t = 0 # reset timeout
            else:
                seqs.remove(c)
            c += 1

        # recv packet
        while 1:
            socks, _, _ = uselect.select([sock], [], [], 0)
            if socks:
                resp = socks[0].recv(4096)
                resp_mv = memoryview(resp)
                h2 = uctypes.struct(uctypes.addressof(resp_mv[20:]), pkt_desc, uctypes.BIG_ENDIAN)
                # TODO: validate checksum (optional)
                seq = h2.seq
                if h2.type==0 and h2.id==h.id and (seq in seqs): # 0: ICMP_ECHO_REPLY
                    #t_elasped = (utime.ticks_us()-h2.timestamp) / 1000
                    t_elasped = abs(utime.ticks_diff(utime.ticks_us(),h2.timestamp) / 1000)
                    ttl = ustruct.unpack('!B', resp_mv[8:9])[0] # time-to-live
                    n_recv += 1
                    not quiet and pprint("%u bytes from %s: icmp_seq=%u, ttl=%u, time=%f ms" % (len(resp), addr, seq, ttl, t_elasped))
                    results.append({ "from": addr,
                                     "bytes": len(resp),
                                     "seq": seq,
                                     "ttl": ttl,
                                     "time": t_elasped
                                    })
                    ping_results.append(t_elasped)
                    seqs.remove(seq)
                    if len(seqs) == 0:
                        finish = True
                        break
            else:
                break

        if finish:
            break

        utime.sleep_ms(1)
        t += 1

    # close
    sock.close()
    ret = (n_trans, n_recv)
    not quiet and pprint("%u packets transmitted, %u packets received" % (n_trans, n_recv))

    result = { "to": host,
               "addr": addr,
               "bytes": len(pkt),
               "n_trans": n_trans,
               "n_recv": n_recv,
               "rtts" : ping_results,
               "pkts": results
                }
    pprint (json.dumps(result))
