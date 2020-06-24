import logging
import asyncio
import time
import json
import socket
import sys
from datetime import datetime

from aiocoap import *

logging.basicConfig(level=logging.INFO)

#server="10.91.124.207"
server="130.243.27.221"

msglen=100

def is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True

async def main():
    """Perform a single PUT request to localhost on the default port, URI
    "/monroe/coap". The request is sent 2 seconds after initialization.

    The payload is bigger than 1kB, and thus sent as several blocks."""

    context = await Context.create_client_context()

    await asyncio.sleep(2)

    #payload = b"The quick brown fox jumps over the lazy dog.\n"

    now=datetime.now()

    #msglen=100
    ts=time.time()
    seq = str(1)
    ts=str(ts)
    left=msglen-(len(seq)+len(ts))
    pad="#"*left
    payload_items=[seq,ts,pad]
    payload=":".join(payload_items)
    payload=payload.encode('ASCII')

    #print (payload)
    #request = Message(code=PUT, payload=payload, uri="coap://10.91.124.207/monroe/coap")
    request = Message(code=PUT, payload=payload, uri="coap://"+server+"/monroe/coap")

    response = await context.request(request).response

    end=datetime.now()

    delay=(end-now).microseconds/1000000
    #print("RTT: ",delay)
    #print('The difference is approx. %s us' % (end-now).microseconds)

    #print('Result: %s\n%r'%(response.code, response.payload))

    owd=float(response.payload.decode().split(":")[1])-float(ts)

    #print ("OWD: ",owd)
    #print (json.dumps({'rtt': delay, 'owd': owd, 'server': server, 'msgLen': msglen}))
    return owd,delay

if __name__ == "__main__":

    if not is_valid_ipv4_address(sys.argv[1]):
    	print("Server ip is not valid.")
    	raise SystemExit
    else:
    	server=sys.argv[1]

    if len(sys.argv) > 2:
        msglen=int(sys.argv[2])
    seq=4
    if len(sys.argv) > 3:
        seq=int(sys.argv[3])
    interval=2
    if len(sys.argv) > 4:
        interval=int(sys.argv[4])
        
    rtts=[]
    owds=[]
    while seq>0:
        output=asyncio.get_event_loop().run_until_complete(main())

        if isinstance(output[0], float):
                owds.append(output[0])
        if isinstance(output[1], float):
                rtts.append(output[1])
        time.sleep(interval)
        seq -=1
    print (json.dumps({'rtt': rtts, 'owd': owds, 'server': server, 'msgLen': msglen}))
