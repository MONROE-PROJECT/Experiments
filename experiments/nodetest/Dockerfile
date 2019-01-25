FROM monroe/base:virt

MAINTAINER Jonas.Karlsson@kau.se

COPY files/* /opt/monroe/

#APT OPTS
ENV APT_OPTS -y --allow-downgrades --allow-remove-essential --allow-change-held-packages --no-install-recommends --no-install-suggests --allow-unauthenticated

############## Kernel Installation (and cleanup) ####################
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install ${APT_OPTS} \
    # Here you would like to install your own kernel of course 
    linux-image-amd64 \
    python-netifaces \
    jq \
    fping \
    net-tools \
    tcpdump \
    curl \
    # Fix missing packages
    && apt-get update ${APT_OPTS} --fix-missing \
    # Cleanup
    && apt-get clean ${APT_OPTS} \
    && apt-get autoremove ${APT_OPTS} \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/doc /usr/share/man /usr/share/locale /var/cache/debconf/*-old firefox.tbz2 geckodriver.tgz dumb-init.deb

# If this container will run as a virtual machine 
# I am here specifying what script to start, have no effect in docker
RUN echo "/bin/bash /opt/monroe/test.sh" >> /opt/monroe/user-experiment.sh

# After the tests are done I poweroff the virtual machine, have no effect in docker 
RUN echo "poweroff" >> /opt/monroe/user-experiment.sh

# This line is executed by docker and is ignored when run a virtual machine
ENTRYPOINT ["/bin/bash", "/opt/monroe/test.sh"]
