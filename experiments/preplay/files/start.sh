#!/bin/bash


cd /opt/monroe/

echo "Experiment starts ..."

make 
	python preplay.py go.com_.json  http
	python preplay.py go.com_.json  https
	python preplay.py go.com_.json  http2

#for i in *.json; do
#	p_rand=echo $((RANDOM%10+1))
#	python preplay.py $i http
#	python preplay.py $i https
#	python preplay.py $i http2

#done

