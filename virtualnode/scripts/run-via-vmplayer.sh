#!/bin/bash
echo "Now booting boot2docker via vmplayer ..."
echo ""
echo "When the image has booted up, please do the following once:"
echo "cd /mnt/hgfs/host/"
echo "./run-virtualnode.sh"
echo ""
vmplayer ../MONROE-VirtualNode.vmx 2> /dev/null
echo "Cleaning up vmware files"
cd ..
rm -f MONROE-VirtualNode.vmxf nvram vmware* MONROE-VirtualNode.vmsd
