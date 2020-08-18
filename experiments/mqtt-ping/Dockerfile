FROM monroe/base

MAINTAINER Jonas.Karlsson@kau.se

COPY files/* /opt/monroe/

#APT OPTS
ENV APT_OPTS -y --allow-downgrades --allow-remove-essential --allow-change-held-packages --no-install-recommends --no-install-suggests --allow-unauthenticated

RUN echo "deb http://repo.mosquitto.org/debian stretch main" > /etc/apt/sources.list.d/mosquitto.list \
    && wget http://repo.mosquitto.org/debian/mosquitto-repo.gpg.key \
    && apt-key add mosquitto-repo.gpg.key \
    && rm -f mosquitto-repo.gpg.key

############## Kernel Installation (and cleanup) ####################
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install ${APT_OPTS} \
    # Need to install a newer libssl
    mosquitto-clients \
    bc \
    jo \
    xxd \
    # Fix missing packages
    && apt-get update ${APT_OPTS} --fix-missing \
    # Cleanup
    && apt-get clean ${APT_OPTS} \
    && apt-get autoremove ${APT_OPTS} \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/doc /usr/share/man /usr/share/locale /var/cache/debconf/*-old firefox.tbz2 geckodriver.tgz dumb-init.deb

# This line is executed by docker and is ignored when run a virtual machine
ENTRYPOINT ["/bin/bash", "/opt/monroe/mqtt_ping.sh"]
