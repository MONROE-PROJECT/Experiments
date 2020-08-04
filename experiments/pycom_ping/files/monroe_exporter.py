#!/usr/bin/python
# -*- coding: utf-8 -*-

# Authors: Jonas Karlsson
# Date: Dec 2015
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

# CODENAME : Unicorn
"""Export json string objects to file."""
import json
import time
from threading import Semaphore, Timer
import os
import tempfile
import argparse
import textwrap
import sys

CMD_NAME = os.path.basename(__file__)
TEMP_FILE_NAME = None
TEMP_FILE = None
FILE_SEMA = Semaphore()
JSON_STORE = []
INITIALIZED = False
DEBUG = False


def initalize(interval, outdir="/monroe/results/"):
    """Bootstrapping timed saves."""
    global INITIALIZED
    if not INITIALIZED:
        _timed_move_to_output_(outdir, interval)
        INITIALIZED = True


def save_output(msg, outdir="/monroe/results/"):
    """Save the msg."""
    global FILE_SEMA, JSON_STORE
    with FILE_SEMA:
        JSON_STORE.append(msg)

    if not INITIALIZED:
        _timed_move_to_output_(outdir, -1)


def _timed_move_to_output_(outdir, interval):
    """Called every interval seconds and move the file to the output directory.

    For later transfer to the remote repository.
    """
    global JSON_STORE, FILE_SEMA

    # Grab the file semaphore so we do not read the CACHE while the other
    # thread is updating it
    with FILE_SEMA:
        if len(JSON_STORE) > 0:
            # Create a name for the file from the first msg in the list
            # and check for obligatory variables
            nodeid = JSON_STORE[0]['NodeId']
            dataid = JSON_STORE[0]['DataId']
            dataversion = JSON_STORE[0]['DataVersion']
            dest_name = outdir + "{}_{}_{}_{}.json".format(nodeid,
                                                           dataid,
                                                           dataversion,
                                                           time.time())

            # A 'atomic copy'
            # copy contents of tmp file to outdir
            # and then rename (atomic operation) to final filename
            statv = os.statvfs(outdir)
            # Only save file if more than 1 Mbyte free
            if statv.f_bfree*statv.f_bsize > 1048576:
                try:
                    tmp_dest_name = None
                    with tempfile.NamedTemporaryFile(mode='w', 
                                                     dir=outdir,
                                                     delete=False,) as tmp_dest:
                        tmp_dest_name = tmp_dest.name

                        for msg in JSON_STORE:
                            try:
                                msg['NodeId']
                                msg['DataId']
                                msg['DataVersion']
                                msg['Timestamp']
                                msg['SequenceNumber']
                                if DEBUG:
                                    print(json.dumps(msg))
                                else:
                                    json.dump(msg, tmp_dest)
                            except Exception as e:
                                errormsg = ("Error: {} {},"
                                            "skipping this message "
                                            "in {}({})").format(e,
                                                                msg,
                                                                tmp_dest_name,
                                                                dest_name)
                                print(errormsg)
                                continue

                        tmp_dest.flush()
                        os.fsync(tmp_dest.fileno())

                    if (os.stat(tmp_dest_name).st_size > 0):
                        # atomic rename of /outdir/tmpXXXX -> /outdir/yyy.json
                        os.rename(tmp_dest_name, dest_name)
                        os.chmod(dest_name, 0o644)
                        JSON_STORE = []
                        # print "Info: Moved {} -> {}".format(tmp_dest_name,
                        #                                    dest_name)
                    else:
                        os.unlink(tmp_dest_name)
                except Exception as e:
                    log_str = "Error: {} {} : {}".format(dest_name,
                                                         tmp_dest_name,
                                                         e)
                    try:
                        os.unlink(tmp_dest_name)
                    except Exception as e:
                        pass
                    print(log_str)
            else:
                # We have too little space left on outdir
                log_str = "Error: Out of disk space: {} ".format(dest_name)
                print(log_str)

    if interval > 1:
        # ..Reschedule me in interval seconds
        t = Timer(interval, lambda: _timed_move_to_output_(outdir, interval))
        t.daemon = True  # Will stop with the main program
        t.start()


def create_arg_parser():
    """Create a argument parser and return it."""
    parser = argparse.ArgumentParser(
        prog=CMD_NAME,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''
            Save experiment/metadata output for later transport
            to repository'''))
    parser.add_argument('--msg',
                        required=True,
                        help=("Experiment/Metadata msg(in JSON format)"
                              "Obligatory keys: NodeId, DataId, DataVersion, "
                              "TimeStamp, SequenceNumber"))
    parser.add_argument('--outdir',
                        metavar='DIR',
                        default="/monroe/results/",
                        help=("Directory to save the results to"
                              "(default /monroe/results/)"))
    parser.add_argument('--debug',
                        action="store_true",
                        help="Do not save files")
    parser.add_argument('-v', '--version',
                        action="version",
                        version="%(prog)s 1.0")
    return parser


if __name__ == '__main__':
    parser = create_arg_parser()
    args = parser.parse_args()
    DEBUG = args.debug
    try:
        jsonmsg = json.loads(args.msg)
        jsonmsg['NodeId']
        jsonmsg['DataId']
        jsonmsg['DataVersion']
        jsonmsg['Timestamp']
        jsonmsg['SequenceNumber']
    except Exception as e:
        errormsg = ("Error: called from commandline with"
                    " invalid JSON got {} : {}").format(args.msg, e)
        print(errormsg)
        sys.exit(1)

    outdir = str(args.outdir)
    if not outdir.endswith('/'):
        print("Info: Corrected missing last / in outdir={}".format(outdir))
        outdir += '/'

    if DEBUG:
        print(("Debug mode: will not insert any posts\n"
              "Info and Statements are printed to stdout\n"
              "{} called with variables \noutdir={}"
              " \nmsg={} \njson={}").format(CMD_NAME,
                                            outdir,
                                            args.msg,
                                            jsonmsg))
    save_output(jsonmsg, outdir)
