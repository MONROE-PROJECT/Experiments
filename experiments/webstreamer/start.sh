#!/bin/bash

cd /webstreamer/files
export PATH=$PATH:/webstreamer/files
./webstreamer  rtsp://217.17.220.110/axis-media/media.amp&
#./webrtc-streamer -H 8888 rtsp://184.72.239.149/vod/mp4:BigBuckBunny_175k.mov rtsp://217.17.220.110/axis-media/media.amp &


lt --port 8000 -s monroe
