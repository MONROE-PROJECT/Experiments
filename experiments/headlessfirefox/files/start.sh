#!/bin/bash


cd /opt/monroe/

export PATH=$PATH:/opt/monroe/

echo "Experiment starts ..."

#!/bin/bash
while IFS='' read -r line || [[ -n "$line" ]]; do
    echo "$line" > one_url
    python headless_browser.py one_url 1 h1
    python headless_browser.py one_url 1 h2
    python headless_browser.py one_url 1 h1s
done < url




