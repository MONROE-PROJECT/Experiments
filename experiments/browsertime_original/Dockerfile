FROM sitespeedio/browsertime

ENV BROWSERTIME_XVFB true
ENV BROWSERTIME_CONNECTIVITY__ENGINE external
ENV BROWSERTIME_DOCKER true
ENV BROWSERTIME_VIDEO true
ENV BROWSERTIME_visualMetrics true

RUN pip install python-dateutil 
RUN pip install pyzmq
RUN pip install netifaces
RUN apt install python-psutil
RUN pip install "flatten_json==0.1.7"
RUN apt install fping

RUN mkdir -p /monroe/results

#COPY files/browsertime-master /opt/monroe/
#COPY files/browsertime-master/browsersupport/ /opt/monroe/basic_browser_repo
COPY files/run_experiment.py /opt/monroe/
COPY files/browsertime.py /opt/monroe/
COPY files/browsertime-dbg.py /opt/monroe/
COPY files/start.sh /opt/monroe/start.sh

WORKDIR /opt/monroe/

ENTRYPOINT ["dumb-init", "--", "/bin/bash", "/opt/monroe/start.sh"]
