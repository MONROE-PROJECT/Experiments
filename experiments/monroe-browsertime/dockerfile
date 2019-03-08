FROM monroe/base:web


#WORKDIR /opt/monroe/
#RUN npm install 

COPY files/browsertime-master /opt/monroe/
COPY files/browsertime-master/browsersupport/ /opt/monroe/basic_browser_repo
COPY files/run_experiment.py /opt/monroe/
COPY files/browsertime.py /opt/monroe/
COPY files/browsertime-dbg.py /opt/monroe/
COPY files/start.sh /opt/monroe/start.sh

ENTRYPOINT ["dumb-init", "--", "/bin/bash", "/opt/monroe/start.sh"]
