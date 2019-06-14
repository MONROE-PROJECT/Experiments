#!/bin/sh
echo "Starting curl mptcp test" >> /outdir/mptcp.check
curl http://www.multipath-tcp.org >> /outdir/mptcp.check
echo "Finished mptcp test, powering off" >> /outdir/mptcp.check
poweroff
