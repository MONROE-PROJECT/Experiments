MONROE-WebRTC container
webstreamer is a docker container based on the source code of WebRTC.

The parameters to use Webstreamer are the following:
- Specify a port with -H using the binary file.
- Specify a STUN server using -S.
- Specify an RTSP link just by running the binary + RTSP Link.
After the container starts please navigate to the https link generated in the container console and go to chrome://webrtcinternals to observer all the metrics in real-time.

Based on the Original WebRTC source code and https://github.com/Mohmoulay/webrtc-streamer.