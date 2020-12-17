#!/bin/bash
set -e

google-chrome --version
firefox --version

# Here's a hack for fixing the problem with Chrome not starting in time
# See https://github.com/SeleniumHQ/docker-selenium/issues/87#issuecomment-250475864

rm -f /var/lib/dbus/machine-id
mkdir -p /var/run/dbus
service dbus restart > /dev/null
service dbus status > /dev/null
export $(dbus-launch)
export NSS_USE_SHARED_DB=ENABLED

# Start adb server and list connected devices
if [ -n "$START_ADB_SERVER" ] ; then
   adb start-server
   adb devices
fi

# Inspired by docker-selenium way of shutting down
function shutdown {
  kill -s SIGTERM ${PID}
  wait $PID
}


cd /opt/monroe/
export PATH=$PATH:/opt/monroe/

START=$(date +%s)

echo -n "Container is starting at $START - "
date

#echo -n "Experiment starts using git version "
#cat VERSION

#ifconfig op0 mtu 1430

python browsertime.py


STOP=$(date +%s)
DIFF=$(($STOP - $START))

echo -n "Container is finished at $STOP - "
date

echo "Container was running for $DIFF seconds"
