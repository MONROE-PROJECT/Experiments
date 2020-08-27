FROM sitespeedio/browsertime

ENV BROWSERTIME_XVFB true
ENV BROWSERTIME_CONNECTIVITY__ENGINE external
ENV BROWSERTIME_DOCKER true
ENV BROWSERTIME_VIDEO true
ENV BROWSERTIME_visualMetrics true
# DumbInit
ENV DI_VER 1.2.2

RUN pip install flatten_json pyzmq
RUN apt install -y python-psutil fping python-netifaces python-dateutil curl dnsutils
RUN curl -L -o dumb-init.deb "https://github.com/Yelp/dumb-init/releases/download/v${DI_VER}/dumb-init_${DI_VER}_amd64.deb" && dpkg -i dumb-init.deb

RUN mkdir -p /monroe/results

COPY files/* /opt/monroe/


ENTRYPOINT ["dumb-init", "--", "/bin/bash", "/opt/monroe/start.sh"]
