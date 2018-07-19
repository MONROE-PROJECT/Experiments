#!/bin/bash

# Manually filter logs the traffic from Marco mobile toward my mobile and whatsapp

tshark -r whatsapp_audio_video_wifi.pcapng -w whatsapp_audio_wifi.pcap -Y  "frame.number < 2419 and udp and ip.src == 192.168.2.17 and not dns and !(ip.dst == 239.255.255.250)" 
tshark -r whatsapp_audio_video_wifi.pcapng -w whatsapp_video_wifi.pcap -Y  "frame.number > 2419 and udp and ip.src == 192.168.2.17 and not dns and !(ip.dst == 239.255.255.250)" 

tshark -r whatsapp_audio_video_3G.pcapng -w whatsapp_audio_3G.pcap -Y  "frame.number < 2181 and udp and ip.src == 192.168.2.17 and not dns and !(ip.dst == 239.255.255.250)" 
tshark -r whatsapp_audio_video_3G.pcapng -w whatsapp_video_3G.pcap -Y  "frame.number > 2181 and udp and ip.src == 192.168.2.17 and not dns and !(ip.dst == 239.255.255.250)" 

tshark -r fbmessanger_audio_video_wifi.pcapng -w fbmessanger_audio_wifi.pcap -Y  "frame.number < 3435 and udp and ip.src == 192.168.2.17 and not dns and !(ip.dst == 239.255.255.250)" 
tshark -r fbmessanger_audio_video_wifi.pcapng -w fbmessanger_video_wifi.pcap -Y  "frame.number > 3435 and udp and ip.src == 192.168.2.17 and not dns and !(ip.dst == 239.255.255.250)" 

tshark -r fbmessanger_audio_video_3G.pcapng -w fbmessanger_audio_3G.pcap -Y  "frame.number < 6750 and udp and ip.src == 192.168.2.17 and not dns and !(ip.dst == 239.255.255.250)" 
tshark -r fbmessanger_audio_video_3G.pcapng -w fbmessanger_video_3G.pcap -Y  "frame.number > 6750 and udp and ip.src == 192.168.2.17 and not dns and !(ip.dst == 239.255.255.250)" 

tshark -r facetime_audio_video_wifi.pcapng -w facetime_audio_wifi.pcap -Y  "frame.number > 26730 and udp and ip.src == 192.168.2.17 and not dns and !(ip.dst == 239.255.255.250)" 
tshark -r facetime_audio_video_wifi.pcapng -w facetime_video_wifi.pcap -Y  "frame.number < 26730 and udp and ip.src == 192.168.2.17 and not dns and !(ip.dst == 239.255.255.250)" 

tshark -r facetime_audio_video_3G.pcapng -w facetime_audio_3G.pcap -Y  "frame.number < 2550 and udp and ip.src == 192.168.2.17 and not dns and !(ip.dst == 239.255.255.250)" 
tshark -r facetime_audio_video_3G.pcapng -w facetime_video_3G.pcap -Y  "frame.number > 2550 and udp and ip.src == 192.168.2.17 and not dns and !(ip.dst == 239.255.255.250)" 
