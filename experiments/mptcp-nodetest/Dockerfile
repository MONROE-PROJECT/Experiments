###################### Final stage ######################################
# Here we make our "normal" image
FROM monroe/base:virt

MAINTAINER jonas.karlsson@kau.se

ENV APT_OPTS -y --allow-downgrades --allow-remove-essential --allow-change-held-packages --allow-unauthenticated

############## Main Installation  ####################
#Copy only the relevant parts from the build stage
COPY --from=docker.cs.kau.se/monroe/containers/mptcp:build /usr/src/*.deb /

# This is the experiment that should run once the vm is started
COPY files/user-experiment.sh /opt/monroe/
RUN chmod ugo+x /opt/monroe/user-experiment.sh

RUN export DEBIAN_FRONTEND=noninteractive \
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install ${APT_OPTS} \
    curl \
    && dpkg -i *.deb \
    && apt-get clean ${APT_OPTS} \
    && apt-get autoremove ${APT_OPTS} \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/doc /usr/share/man /usr/share/locale /var/cache/debconf/*-old *.deb


############## Tweaks  ####################
RUN echo "root:toor"| chpasswd
