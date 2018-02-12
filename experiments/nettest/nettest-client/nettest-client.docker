FROM monroe/base

MAINTAINER cise@simula.no

ARG BUILD_DEPS="git autoconf automake make gcc pkg-config libjson-c-dev libssl-dev uuid-dev liblzma-dev"
ARG PKG_DEPS="libuuid1 traceroute"

RUN mkdir -p /opt/monroe

COPY nettest-core /opt/monroe/nettest-core

RUN export DEBIAN_FRONTEND=noninteractive && apt-get update && apt-get install -y --force-yes --no-install-recommends --no-install-suggests \
  $BUILD_DEPS $PKG_DEPS \
  && cd /opt/monroe/nettest-core && ./autobuild.sh && make install && cd /opt/monroe && rm -rf nettest-client \
  && apt-get purge -y --force-yes $BUILD_DEPS \
  && apt-get clean -y --force-yes clean \
  && apt-get -y --force-yes autoremove \
  && rm -rf /var/lib/apt/lists/* /tmp/*

# allow -i option to traceroute for non-root users:
RUN setcap cap_net_raw+ep /usr/bin/traceroute.db

COPY files/* /opt/monroe/

ENTRYPOINT ["dumb-init", "--", "/usr/bin/python", "/opt/monroe/nettest.py"]
