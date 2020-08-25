FROM sitespeedio/browsertime

ENV BROWSERTIME_XVFB true
ENV BROWSERTIME_CONNECTIVITY__ENGINE external
ENV BROWSERTIME_DOCKER true
ENV BROWSERTIME_VIDEO true
ENV BROWSERTIME_visualMetrics true

RUN pip install flatten_json pyzmq
RUN apt install -y python-psutil fping python-netifaces python-dateutil

RUN mkdir -p /monroe/results

COPY files/* /opt/monroe/

WORKDIR /opt/monroe/

ENTRYPOINT ["dumb-init", "--", "/bin/bash", "/opt/monroe/start.sh"]
