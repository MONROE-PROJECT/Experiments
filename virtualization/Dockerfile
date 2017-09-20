FROM monroe/base

MAINTAINER jonas.karlsson@kau.se

ENV APT_OPTS -y --allow-downgrades --allow-remove-essential --allow-change-held-packages --no-install-recommends --no-install-suggests --allow-unauthenticated

# This is the experiment that should run once the vm is started
COPY files/experiment.sh /opt/monroe/
RUN chmod ugo+x /opt/monroe/experiment.sh

# These files are from http://multipath-tcp.org/pmwiki.php/Users/ConfigureRouting
COPY files/mptcp_up /etc/network/if-up.d/
COPY files/mptcp_down /etc/network/if-post-down.d/
RUN chmod ugo+x /etc/network/if-up.d/mptcp_up
RUN chmod ugo+x /etc/network/if-post-down.d/mptcp_down


############## Main Installation (and cleanup) ####################
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install ${APT_OPTS} \
    linux-image-amd64 \
    grub2 \
    sysvinit-core \
    ifupdown \
    irqbalance \
    udev \
    # Fix missing packages
    && apt-get update ${APT_OPTS} --fix-missing \
    # Cleanup
    && apt-get clean ${APT_OPTS} \
    && apt-get autoremove ${APT_OPTS} \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/doc /usr/share/man /usr/share/locale /var/cache/debconf/*-old firefox.tbz2 geckodriver.tgz dumb-init.deb

############## Tweaks  ####################
RUN echo "root:toor"| chpasswd \
    && echo "blacklist vga16fb" > /etc/modprobe.d/blacklist-framebuffer.conf \
    && sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="quiet"/GRUB_CMDLINE_LINUX_DEFAULT="net.ifnames=0 biosdevname=0 fbcon=map:99 text"/g' /etc/default/grub \
    && sed -i 's/GRUB_CMDLINE_LINUX=""/GRUB_CMDLINE_LINUX="net.ifnames=0 biosdevname=0 fbcon=map:99 text"/g' /etc/default/grub \
    && sed -i 's/GRUB_TIMEOUT=5/GRUB_TIMEOUT=0/g' /etc/default/grub \
    && sed -i 's/#GRUB_TERMINAL=console/GRUB_TERMINAL=console/g' /etc/default/grub \
    && sed -i 's,# By default this script does nothing.,# By default this script does nothing.\n/opt/monroe/experiment.sh || exit 1,g' /etc/rc.local \
