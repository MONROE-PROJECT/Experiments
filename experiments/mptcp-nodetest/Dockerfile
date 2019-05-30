
# There are three ways to install a custom kernel:
# 1. Copy the -deb files from a image with a precompiled kernel
#      * MPTCP example can be found in subfolder build
# 2. (as we do here) Do the compilation at build time (will be time consuming for big projects like a kernel)
#      * Example Dockerfile_allione
# 3. Build the kernel outside and copy the files into the image

###################### Build stage ######################################
# Here we build the kernel
FROM debian:stretch AS build

MAINTAINER jonas.karlsson@kau.se

ENV APT_OPTS -y --allow-downgrades --allow-remove-essential --allow-change-held-packages --allow-unauthenticated

#Add the src files to the repo list
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

RUN rm -f /usr/src/*dbg*

###################### End Build stage ##################################

###################### Final stage ######################################
# Here we make our "normal" image
FROM monroe/base:virt

MAINTAINER jonas.karlsson@kau.se

ENV APT_OPTS -y --allow-downgrades --allow-remove-essential --allow-change-held-packages --allow-unauthenticated

############## Main Installation  ####################
#Copy only the relevant parts from the build stage
COPY --from=build /usr/src/*.deb /

# This is the experiment that should run once the vm is started
COPY files/user-experiment.sh /opt/monroe/
RUN chmod ugo+x /opt/monroe/user-experiment.sh

RUN export DEBIAN_FRONTEND=noninteractive \
    && dpkg -i *.deb \
    && apt-get clean ${APT_OPTS} \
    && apt-get autoremove ${APT_OPTS} \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/doc /usr/share/man /usr/share/locale /var/cache/debconf/*-old *.deb


############## Tweaks  ####################
RUN echo "root:toor"| chpasswd