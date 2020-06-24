FROM monroe/base

MAINTAINER mohammad.rajiullah@kau.se




#APT OPTS
ENV APT_OPTS -y --allow-downgrades --allow-remove-essential --allow-change-held-packages --no-install-recommends --no-install-suggests --allow-unauthenticated

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install ${APT_OPTS} \
       python3-aiocoap \
   # &&	pip3 install LinkHeader \
     # Fix missing packages
    && apt-get update ${APT_OPTS} --fix-missing \
    # Cleanup
    && apt-get clean ${APT_OPTS} \
    && apt-get autoremove ${APT_OPTS} \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/doc /usr/share/man /usr/share/locale /var/cache/debconf/*-old firefox.tbz2 geckodriver.tgz dumb-init.deb

WORKDIR /opt/monroe/
	
	

COPY files/* /opt/monroe/

ENTRYPOINT ["dumb-init", "--", "/bin/bash", "/opt/monroe/start.sh"]
