FROM monroe/base

MAINTAINER Jonas.Karlsson@kau.se

RUN pip install flatten_json
#RUN pip3 install flatten_json
COPY files/* /opt/monroe/

ENTRYPOINT ["dumb-init", "--", "/usr/bin/python", "/opt/monroe/experiment.py"]
