FROM monroe/base:web

RUN apt-get update -y && apt-get install -y \
  imagemagick \
  python-pil \
  python-numpy \
  python-scipy \
  python-matplotlib \
  python-pandas \
  python-pip \
  python-sympy \
  python-nose \
  --no-install-recommends --force-yes && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
  python -m pip install pyssim && \
  wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
  tar --strip-components 1 -C /usr/bin -xf ffmpeg-release-amd64-static.tar.xz --wildcards */ffmpeg */ffprobe && \
  rm ffmpeg-release-amd64-static.tar.xz && \
  apt-get purge -y --auto-remove python-pip

#WORKDIR /opt/monroe/
#RUN npm install 
ENV BROWSERTIME_XVFB true
ENV BROWSERTIME_CONNECTIVITY__ENGINE external
ENV BROWSERTIME_DOCKER true
ENV BROWSERTIME_VIDEO true
ENV BROWSERTIME_visualMetrics true


COPY files/browsertime-master /opt/monroe/
COPY files/browsertime-master/browsersupport/ /opt/monroe/basic_browser_repo
COPY files/run_experiment.py /opt/monroe/
COPY files/browsertime.py /opt/monroe/
COPY files/browsertime-dbg.py /opt/monroe/
COPY files/start.sh /opt/monroe/start.sh

ENTRYPOINT ["dumb-init", "--", "/bin/bash", "/opt/monroe/start.sh"]
