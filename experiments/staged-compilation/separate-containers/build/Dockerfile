FROM debian:stretch

MAINTAINER jonas.karlsson@kau.se

ENV APT_OPTS -y --allow-downgrades --allow-remove-essential --allow-change-held-packages --allow-unauthenticated

RUN cat /etc/apt/sources.list > stmp \
    && sed 's/deb /deb-src /g' stmp >> /etc/apt/sources.list \
    && rm stmp

############## Main Installation  ####################
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get upgrade ${APT_OPTS} \
    && apt-get install ${APT_OPTS} \
    build-essential \
    fakeroot \
    git \
    linux-image-amd64 \
    lsb-release \
    && apt-get ${APT_OPTS} build-dep linux

#Clone mptcp git
RUN mkdir -p /usr/src/
RUN git clone --depth=1 git://github.com/multipath-tcp/mptcp.git /usr/src/kernel-source

WORKDIR /usr/src/kernel-source
# Can only be one but that is also the case since we only install one kernel
RUN cp /boot/config-* .config

#Enable mptcp
COPY files/config_mptcp.sh /usr/src/kernel-source/
RUN bash config_mptcp.sh

RUN yes '' | make oldconfig

RUN scripts/config --disable DEBUG_INFO

RUN make clean
RUN make -j `getconf _NPROCESSORS_ONLN` deb-pkg LOCALVERSION=-mptcp
