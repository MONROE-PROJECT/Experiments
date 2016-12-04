#!/bin/bash


cd /opt/monroe/
export PATH=$PATH:/opt/monroe/

echo "Experiment starts ..."

python headless_browser_with_user_input.py
#while IFS='' read -r line || [[ -n "$line" ]]; do
#    echo "$line" > one_url
#    python headless_browser.py one_url 1 h1
#    python headless_browser.py one_url 1 h2
#    python headless_browser.py one_url 1 h1s
#done < url

tar -zcvf /monroe/results/results$RANDOM.tgz /tmp/*.json
#python headless_browser.py one_url 10 h1






