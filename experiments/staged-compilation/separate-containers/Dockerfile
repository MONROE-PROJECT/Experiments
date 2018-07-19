# There are three ways to install a custom kernel:
# 1. (as we do here) copy the -deb files from a image with a precompiled kernel
#      * MPTCP example can be found in subfolder build
# 2. Do the compilation at build time (will be time consuming for big projects like a kernel)
#      * Example Dockerfile_allione
# 3. Build the kernel outside and copy the files into the image

#This container is a build environment that also holds a precompiled version of the mptcp kernel
FROM build AS build

#Delete the debug kernels/sysmbols and such
RUN rm -f /usr/src/*dbg*

# Maybe do some stuff here like adding patches, recompiling if necessary
# Do not run make clean or make distclean unless super important

# Here we make our "vm" image
FROM monroe/base:virt

MAINTAINER jonas.karlsson@kau.se

ENV APT_OPTS -y --allow-downgrades --allow-remove-essential --allow-change-held-packages --allow-unauthenticated

############## Main Installation  ####################
# Copy the kernel deb files from our build image
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
# This will create a login so you can debug the vm locally not necessary on the final image
RUN echo "root:toor"| chpasswd
