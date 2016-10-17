#!/bin/bash


cd /opt/monroe/

echo "Experiment starts ..."


if [ -d "har/" ]; then
  rm har/*.har
fi

python headless_browser.py url 1 h2

if [ -d "har/" ]; then
  rm har/*.har
fi
python headless_browser.py url 1 h1s


