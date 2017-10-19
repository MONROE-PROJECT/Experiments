#!/bin/bash
# Get boot2docker
curl -s https://api.github.com/repos/boot2docker/boot2docker/releases/latest | jq -r ".assets[] | select(.name | test(\"boot2docker.iso\")) | .browser_download_url"| tr -d " "|xargs -n1 curl -L -o ../boot2docker.iso
