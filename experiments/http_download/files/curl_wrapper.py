#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Jonas Karlsson
# Date: Sept 2015
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

# CODENAME : Rainbow

r"""
Simple curl wrapper download a url/file using curl.

The output will be formated into a json object suitable for storage in the
MONROE db.
"""
import json
import time
import os
import argparse
import textwrap
import syslog
from subprocess import check_output, CalledProcessError

CMD_NAME = os.path.basename(__file__)

def run_exp(curl_cmd, interface, debug):
    """Run the experiment and collect the output."""
    try:
        output = check_output(curl_cmd)
        # Clean away leading and trailing whitespace
        output = output.strip(' \t\r\n\0')
        # Convert to JSON
        msg = json.loads(output)
        # Should be replaced with real value from "scheduler"/initscript
        GUID = "{}.{}.{}.{}".format("experiment_id",
                                    "scheduling_id",
                                    "node_id",
                                    "repetition")
        msg.update({
            "Guid": GUID,
            "TimeStamp": time.time(),
            "InterfaceName": interface,
            "DownloadTime": msg["TotalTime"] - msg["SetupTime"]
        })
        print (msg) if (debug) else monroe_exporter.save_output(msg)
    except CalledProcessError as e:
        log_str = "Execution failed: {}".format(e)
        print (msg) if (debug) else syslog.syslog(log_str)


def create_arg_parser():
    """Create a argument parser and return it."""
    parser = argparse.ArgumentParser(
        prog=CMD_NAME,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''
            Download a specified file/url via and parses the output into json
            objects suitable for monore db import.
            The download will finish when either:
            --time or ---size or the complete URL is downloaded
            '''))
    parser.add_argument('--interface',
                        required=True,
                        help="Which interface to bind to")
    parser.add_argument('--timeout',
                        required=True,
                        type=int,
                        help="Max time a download can take (s).")
    parser.add_argument('--url',
                        default="http://speedtest.bahnhof.net/1000M.zip",
                        help="The url/file to download.")
    parser.add_argument('--size',
                        type=int,
                        required=True,
                        help="Max size to download (MB).")
    parser.add_argument('--interval',
                        metavar='N',
                        type=int,
                        default=600,
                        help="Seconds between runs")
    parser.add_argument('--debug',
                        action="store_true",
                        help="Do not save any results")
    parser.add_argument('-v', '--version',
                        action="version",
                        version="%(prog)s 1.0")
    return parser


if __name__ == '__main__':
    parser = create_arg_parser()
    args = parser.parse_args()

    data_id = 'MONROE.EXP.HTTP.DOWNLOAD'
    data_version = 1
    interval = args.interval
    export_interval = interval*5  # 4 experiment runs in each json file
    size = args.size*1024 - 1  # Convert from KB and remove first byte
    timeout = args.timeout
    interface = args.interface
    url = args.url
    debug = args.debug
    # What to save
    curl_metrics = ('{ '
                    '"Host": "%{remote_ip}", '
                    '"Port": "%{remote_port}", '
                    '"Speed": %{speed_download}, '
                    '"Bytes": %{size_download}, '
                    '"TotalTime": %{time_total}, '
                    '"SetupTime": %{time_starttransfer} '
                    '}')
    # This is the experiment command
    cmd = ["curl",
           "--raw",
           "--silent",
           "--write-out", "{}".format(curl_metrics),
           "--interface", "{}".format(interface),
           "--max-time", "{}".format(timeout),
           "--range", "0-{}".format(size),
           "{}".format(url)]

    # Initialize export functions
    log_str = ("Initialize experiment : "
               "DataId : {}, "
               "DataVersion : {}, "
               "Repeat every {} s, "
               "Export results every {}").format(data_id,
                                                 data_version,
                                                 interval,
                                                 export_interval)
    if (debug):
        print (log_str)
    else:
        import monroe_exporter
        monroe_exporter.initalize(data_id, data_version, export_interval)

    # Run the experiment "forever"
    while True:
        start_time = time.time()

        log_str = "Starting Experiment Run : {}".format(cmd)
        print(log_str) if (debug) else syslog.syslog(log_str)

        run_exp(cmd, interface, debug)

        elapsed = time.time() - start_time
        # Wait if interval > 0 else break loop
        if (interval > 0):
            wait = interval - elapsed if (interval - elapsed > 0) else 0
            log_str = "Now waiting {} s before next run".format(wait)
            print (log_str) if (debug) else syslog.syslog(log_str)
            time.sleep(wait)
        else:
            log_str = "Finsished after {}".format(elapsed)
            print (log_str) if (debug) else syslog.syslog(log_str)
            # The loop ends here
            break
