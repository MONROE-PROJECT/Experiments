#!/bin/sh
echo "Starting curl mptcp test" >> /outdir/mptcp.check
curl http://www.multipath-tcp.org >> /outdir/mptcp.check
