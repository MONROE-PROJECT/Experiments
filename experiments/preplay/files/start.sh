#!/bin/bash


cd /opt/monroe/

echo "Experiment starts ..."

make 

for i in *.json; do
#	p_rand=echo $((RANDOM%10+1))
	python preplay.py $i http
	python preplay.py $i https
	python preplay.py $i http2

done

