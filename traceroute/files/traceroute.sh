#!/bin/bash

#ParisTracerouteTargets="www.ntua.gr www.uc3m.es www.kth.se Google.com Facebook.com Youtube.com Baidu.com Yahoo.com Amazon.com Wikipedia.org Google.co.in Qq.com Twitter.com"

ParisTracerouteTargetsPopular=" dropbox.com s.yimg.com s.ytimg.com ep01.epimg.net elpais.com video-mad1-1.xx.fbcdn.net scontent-mad1-1.xx.fbcdn.net external-mad1-1.xx.fbcdn.net graph.facebook.com static.xx.fbcdn.net m.facebook.com www.facebook.com sync.liverail.com scontent-mad1-1.cdninstagram.com graph.instagram.com instagramstatic-a.akamaihd.net scontent-mad1-1.cdninstagram.com staticxx.facebook.com s0.2mdn.net estaticos.marca.com e02-marca.uecdn.es ds.serving-sys.com tpc.googlesyndication.com scontent.xx.fbcdn.net graph.facebook.com 31.13.83.2 audio-ec.spotify.com 194.132.197.210 heads-fab.spotify.com i.scdn.co images.gotinder.com api.gotinder.com 93.184.220.66 mmi675.whatsapp.net mme.whatsapp.net wikipedia.org upload.wikimedia.org i.ytimg.com r7---sn-h5q7dn7r.googlevideo.com r1---sn-h5q7dn7r.googlevideo.com r4---sn-h5q7dne6.googlevideo.com youtubei.googleapis.com googleapis.com"

#ParisTracerouteTargets="www.uc3m.es"
interfaces="op0"
DATE=$(date +%s+%N)

for TARGET in $ParisTracerouteTargetsPopular
do
for interface in $interfaces
do
echo $interface > sourceInterface.txt
python /opt/foivos/getInterfaceIP.py $interface
cp /sourceI* /opt/foivos/ # we copy the files just to be sure that paris-traceroute can find them
#mv sourceInterface.txt /opt/foivos/sourceInterface.txt # paris-traceroute will look for these files in the working directory, which is "/" not in /opt/foivos
#mv sourceIP.txt /opt/foivos/sourceIP.txt
StartTime=$(date +%s) # date in seconds without miliseconds
/opt/foivos/paris-traceroute -n -a exh -p icmp $TARGET &> /opt/foivos/ExhaustiveParisTracerouteOutput-$DATE-$TARGET-$interface-result.txt 
EndTime=$(date +%s) # date in seconds without miliseconds

/usr/bin/python /opt/foivos/trace.py --targetDomainName $TARGET \
--fileToParse /opt/foivos/ExhaustiveParisTracerouteOutput-$DATE-$TARGET-$interface-result.txt \
--productionTestingSwitch production \
--JsonTracetouteSwitch traceroute \
--startTime $StartTime \
--endTime $EndTime \
--tracerouteMode paris_traceroute_exhaustive \
--InterfaceName $interface

toMove=$(ls -t *.json | head -1)
cp $toMove /monroe/results/$toMove.tmp
mv /monroe/results/$toMove.tmp /monroe/results/$toMove

StartTime=$(date +%s) # date in seconds without miliseconds
traceroute -i $interface $TARGET &> /opt/foivos/SimpleTracerouteOutput-$DATE-$TARGET-$interface-result.txt 
EndTime=$(date +%s) # date in seconds without miliseconds

/usr/bin/python /opt/foivos/trace.py --targetDomainName $TARGET \
--fileToParse /opt/foivos/SimpleTracerouteOutput-$DATE-$TARGET-$interface-result.txt \
--productionTestingSwitch production \
--JsonTracetouteSwitch traceroute \
--startTime $StartTime \
--endTime $EndTime \
--tracerouteMode simple_traceroute \
--InterfaceName $interface

toMove=$(ls -t *.json | head -1)
cp $toMove /monroe/results/$toMove.tmp
mv /monroe/results/$toMove.tmp /monroe/results/$toMove
done
done

sleep 30
