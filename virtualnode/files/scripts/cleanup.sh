#!/bin/sh
export PATH=/usr/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Cleanup
find -L /var/run/netns -type l -delete
rm -f /var/run/netns/monroe
