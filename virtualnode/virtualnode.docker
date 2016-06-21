FROM monroe/base

MAINTAINER jonas.karlsson@kau.se

RUN mkdir -p /opt/monroe
RUN mkdir -p /monroe

COPY files/* /opt/monroe/

# Default cmd to run
ENTRYPOINT ["dumb-init", "--", "/bin/bash", "/opt/monroe/run.sh"]
