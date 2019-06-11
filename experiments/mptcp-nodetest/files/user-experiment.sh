#!/bin/sh
echo "Starting curl mptcp test" >> /monroe/results/mptcp.check
curl http://www.multipath-tcp.org >> /monroe/results/mptcp.check
