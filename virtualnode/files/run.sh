#!/bin/bash
# Setup networks
brctl addbr usb0
brctl addbr usb1
brctl addbr usb2

brctl addif usb0 eth0
brctl addif usb1 eth0
brctl addif usb2 eth0


while true; do sleep 300; done
