FROM monroe/base

MAINTAINER Jonas.Karlsson@kau.se

COPY files/* /opt/monroe/



############## Install pyserial  ####################
ENV APT_OPTS -y --allow-downgrades --allow-remove-essential --allow-change-held-packages --no-install-recommends --no-install-suggests --allow-unauthenticated
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install ${APT_OPTS} \
    python3-serial \
    && apt-get update ${APT_OPTS} --fix-missing \
    # Cleanup
    && apt-get clean ${APT_OPTS} \
    && apt-get autoremove ${APT_OPTS} \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/doc /usr/share/man /usr/share/locale /var/cache/debconf/*-old

WORKDIR /opt/monroe
ENTRYPOINT ["dumb-init", "--", "/usr/bin/python3", "/opt/monroe/pycom_ping.py"]
