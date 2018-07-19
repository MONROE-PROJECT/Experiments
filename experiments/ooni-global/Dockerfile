FROM monroe/base

RUN echo 'deb http://ftp.uk.debian.org/debian/ stretch main contrib non-free' \
      > /etc/apt/sources.list
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y ooniprobe patch python-pyroute2 python-ipaddress python-scapy && apt clean
COPY files/* /opt/monroe/
RUN patch -p1 < /opt/monroe/patch.1
RUN patch -p1 < /opt/monroe/patch.2
ENTRYPOINT ["dumb-init", "--", "/opt/monroe/runme.py"]
