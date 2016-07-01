import pyotp
import time
import urllib
import urllib2
import json
from os import chmod
from Crypto.PublicKey import RSA

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
        print "Missing expconfig variable {}".format(e)
        raise e

    # Create the ssh keys
    key = RSA.generate(2048)
    pubkey = key.publickey()
    if not DEBUG:
        with open("/root/.ssh/id_rsa", 'w') as content_file:
            chmod("/root/.ssh/id_rsa", 0600)
            content_file.write(key.exportKey('PEM'))

        with open("/root/.ssh/id_rsa.pub", 'w') as content_file:
            content_file.write(pubkey.exportKey('OpenSSH'))
        with open("/root/.ssh/authorized_keys", 'w') as content_file:
            content_file.write(pubkey.exportKey('OpenSSH'))

    params = {
                'token': token,
                'nodeid': nodeid,
                'guid': guid,
                'pubkey': pubkey.exportKey('OpenSSH'),  # generated
                'enddate': stop  # end date from scheduler
         }
try:
    res = urllib2.urlopen(url="http://{}:{}".format(server, port),
                          data=urllib.urlencode(params))
    retur = json.loads(res.read())
    if not DEBUG:
        with open("/root/.ssh/known_hosts", 'w') as content_file:
            content_file.write(retur['hostkey'])
    while True:
        print "ssh -fN -R {}:localhost:22 {}@{}".format(retur['port'],
                                                        retur['user'],
                                                        retur['server'])
        print key.exportKey('PEM')
        time.sleep(300)
except Exception as e:
    print "{}".format(e)
    raise e
