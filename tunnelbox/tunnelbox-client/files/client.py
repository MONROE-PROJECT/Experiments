import pyotp
import time
import urllib
import urllib2
import json
import sys
import httplib


# Configuration
DEBUG = False
CONFIGFILE = '/monroe/config'

# Default values (overwritable from the scheduler)
# Can only be updated from the main thread and ONLY before any
# other processes are started
EXPCONFIG = {
        "server": "localhost",
        "nodeid": "0",
        "guid": "no.guid.in.file",
        "token": pyotp.TOTP("INKF26AB345PESNF").now(),
        "certfile": "",
        "webport": 9000,
        "verbosity": 2,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "start": time.time(),
        "stop": time.time()+3600*24  # end date from scheduler
        }


if __name__ == '__main__':
    """The main thread control the processes (experiment/metadata)."""

    if len(sys.argv) < 2:
            print "Need IP to BIND"
            sys.exit(1)

    SOURCE_IP = sys.argv[1]

    if not DEBUG:
        # Try to get the experiment config as provided by the scheduler
        try:
            with open(CONFIGFILE) as configfd:
                EXPCONFIG.update(json.load(configfd))
        except Exception as e:
            raise e
    else:
        # We are in debug state always put out all information
        EXPCONFIG['verbosity'] = 3
        EXPCONFIG['resultdir'] = "./"

    # Short hand variables and check so we have all variables we need
    try:
        server = EXPCONFIG['server']
        token = EXPCONFIG['token']
        port = EXPCONFIG['webport']
        verbosity = EXPCONFIG['verbosity']
        sslcert = EXPCONFIG['certfile']
        stop = EXPCONFIG["stop"]
        nodeid = EXPCONFIG["nodeid"]
        guid = EXPCONFIG["guid"]
    except Exception as e:
        raise e

    # Read the ssh keys
    with open('/root/.ssh/id_rsa.pub', 'r') as f:
        pubkey = f.readline().strip()

    params = {
                'token': token,
                'nodeid': nodeid,
                'guid': guid,
                'pubkey': pubkey,
                'enddate': stop  # end date from scheduler
         }
try:
    # Lets go bananas and MONKEYPATCH httplib so urllib2 can bind to ip
    HTTPSConnection_real = httplib.HTTPSConnection

    class HTTPSConnection_monkey(HTTPSConnection_real):
        def __init__(*a, **kw):
            HTTPSConnection_real.__init__(*a, source_address=(SOURCE_IP, 0), **kw)
    httplib.HTTPSConnection = HTTPSConnection_monkey
    # End MONKEYPATCH

    res = urllib2.urlopen(url="http://{}:{}".format(server, port),
                          data=urllib.urlencode(params))
    retur = json.loads(res.read())
    if not DEBUG:
        with open("/root/.ssh/known_hosts", 'w') as content_file:
            content_file.write(retur['hostkey'])

    print '-R *:{}:localhost:22 {}@{}'.format(retur['port'],
                                              retur['user'],
                                              retur['server'])
except Exception as e:
    raise e
