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
import syslog
import sys

CMD_NAME = os.path.basename(__file__)
TEMP_FILE_NAME = None
TEMP_FILE = None
FILE_SEMA = Semaphore()
NODEID = None
JSON_STORE = []

try:
    with open("/nodeid") as nid:
        NODEID = nid.readline().strip()
except Exception as e:
    syslog.syslog(syslog.LOG_ERR, "Cannot retrive Nodeid {}".format(e))
    raise e


def initalize(dataid, dataversion, interval, outdir="/outdir/"):
    """Bootstrapping timed saves."""
    _timed_move_to_output_(dataid, dataversion, outdir, interval)


def save_output(msg,
                dataid=None,
                dataversion=None,
                outdir="/outdir/"):
    """Save the msg."""
    with FILE_SEMA:
        JSON_STORE.append(msg)
    if (dataid and dataversion):
        _timed_move_to_output_(dataid, dataversion, outdir, -1)


def _timed_move_to_output_(dataid, dataversion, outdir, interval=-1):
    """Called every interval seconds and move the file to the output directory.

    For later transfer to the remote repository.
    """
    global JSON_STORE
    # Grab the file semaphore
    # so we do not move the file while the other thread is writing
    with FILE_SEMA:
        if len(JSON_STORE) == 0:
            syslog.syslog(syslog.LOG_INFO, "No JSONS, not moving")
        else:
            # Create a name for the file
            dest_name = outdir + "{}_{}_{}_{}.json".format(NODEID,
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
                    with tempfile.NamedTemporaryFile(dir=outdir,
                                                     delete=False) as tmp_dest:
                        tmp_dest_name = tmp_dest.name

                        for msg in JSON_STORE:
                            msg['NodeId'] = NODEID
                            msg['DataId'] = dataid
                            msg['DataVersion'] = dataversion
                            print >> tmp_dest, json.dumps(obj=msg)
                            # print json.dumps(obj=msg)

                        tmp_dest.flush()
                        os.fsync(tmp_dest.fileno())

                    # atomic rename of /outdir/tmpXXXX -> /outdir/yyy.json
                    os.rename(tmp_dest_name, dest_name)
                    os.chmod(dest_name, 0644)
                    JSON_STORE = []
                    syslog.syslog(syslog.LOG_INFO,
                                  "Moved {} -> {}".format(tmp_dest_name,
                                                          dest_name))
                except Exception as e:
                    log_str = "Error {} {} : {}".format(dest_name,
                                                        tmp_dest_name,
                                                        e)
                    syslog.syslog(syslog.LOG_ERR, log_str)
                    print log_str
            else:
                # We have too little space left on outdir
                log_str = "Out of disk space : {} ".format(dest_name)
                syslog.syslog(syslog.LOG_ERR, log_str)
                print log_str

    if interval > 1:
        # ..Reschedule me in interval seconds
        t = Timer(interval, lambda: _timed_move_to_output_(dataid,
                                                           dataversion,
                                                           outdir,
                                                           interval))
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
    parser.add_argument('--dataid',
                        required=True,
                        help="DataId of the experiment/metdata")
    parser.add_argument('--dataversion',
                        default=1,
                        help=("DataVersion of the experiment/metdata"
                              "(default 1)"))
    parser.add_argument('--msg',
                        required=True,
                        help="Experiment/Metadata msg (in JSON format)")
    parser.add_argument('--outdir',
                        metavar='DIR',
                        default="/outdir/",
                        help=("Directory to save the results to"
                              "(default /outdir/)"))
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

    try:
        jsonmsg = json.loads(args.msg)
    except Exception as e:
        errormsg = ("Error called from commandline with"
                    " invalid JSON got {} : {}").format(args.msg, e)
        syslog.syslog(syslog.LOG_ERR, errormsg)
        print errormsg
        sys.exit(1)

    outdir = str(args.outdir)
    if not outdir.endswith('/'):
        infomsg = ("Corrected missing last / in outdir={}, "
                   "data={}, dataversion={}").format(outdir,
                                                     args.dataid,
                                                     args.dataversion)
        syslog.syslog(syslog.LOG_INFO, infomsg)
        print infomsg
        outdir += '/'

    if not args.debug:
        save_output(jsonmsg,
                    args.dataid,
                    args.dataversion,
                    outdir)
    else:
        print("Debug mode: will not insert any posts or create any files\n"
              "Info and Statements are printed to stdout\n"
              "{} called on node {} with variables \ndataid={}"
              "\ndataversion={} \noutdir={}"
              " \nmsg={} \njson={}").format(CMD_NAME,
                                            NODEID,
                                            args.dataid,
                                            args.dataversion,
                                            outdir,
                                            args.msg,
                                            jsonmsg)
