FROM monroe/base:staging

MAINTAINER jonas.karlsson@kau.se

ENV APT_OPTS -y --allow-downgrades --allow-remove-essential --allow-change-held-packages --no-install-recommends --no-install-suggests --allow-unauthenticated

COPY files/* /opt/monroe/
RUN chmod ugo+x /opt/monroe/experiment.sh

############## Main Installation (and cleanup) ####################
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install ${APT_OPTS} \
    linux-image-amd64 \
    grub2 \
    sysvinit-core \
    # Fix missing packages
    && apt-get update ${APT_OPTS} --fix-missing \
    # Cleanup
    && apt-get clean ${APT_OPTS} \
    && apt-get autoremove ${APT_OPTS} \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/doc /usr/share/man /usr/share/locale /var/cache/debconf/*-old firefox.tbz2 geckodriver.tgz dumb-init.deb

############## Tweaks  ####################
RUN echo "root:toor"| chpasswd \
    && sed -i s/GRUB_CMDLINE_LINUX_DEFAULT=\"quiet\"/GRUB_CMDLINE_LINUX_DEFAULT=\"\"/g /etc/default/grub \
    && sed -i 's,# By default this script does nothing.,# By default this script does nothing.\n/opt/monroe/experiment.sh || exit 1,g' /etc/rc.local
