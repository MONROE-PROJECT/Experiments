#!/bin/bash

cd /opt/monroe
python publisher.py &
while true; do sleep 300; done
