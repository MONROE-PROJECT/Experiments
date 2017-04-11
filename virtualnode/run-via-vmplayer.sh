#!/bin/bash
# Get boot2docker
curl -s https://api.github.com/repos/boot2docker/boot2docker/releases/latest | jq -r ".assets[] | select(.name | test(\"boot2docker.iso\")) | .browser_download_url"| tr -d " "|xargs -n1 curl -L -o boot2docker.iso

echo "Now booting boot2docker via vmplayer ..."
echo ""
echo "When the image has booted up, please do the following once:"
echo "cd /mnt/hgfs/host/"
echo "./init.sh"
echo ""
vmplayer MONROE-VirtualNode.vmx
#vmplayer MONROE-VirtualNode.vmx 2> /dev/null
#echo "Cleaning up vmware files"
#rm -f MONROE-VirtualNode.vmxf nvram vmware* MONROE-VirtualNode.vmsd
