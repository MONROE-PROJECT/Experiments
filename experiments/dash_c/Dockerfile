
###################### Build stage ######################################
# Here we build dashc : https://github.com/uccmisl/dashc.git
FROM ubuntu:18.04 AS build

MAINTAINER jonas.karlsson@kau.se

# From configure in https://github.com/uccmisl/dashc.git
ENV BUILD_DEP="bubblewrap m4 git net-tools wget mercurial darcs libcap-dev unzip sed pkg-config libffi-dev libssl-dev"

ENV DEBIAN_FRONTEND=noninteractive
ENV APT_OPTS -y --allow-downgrades --allow-remove-essential --allow-change-held-packages --allow-unauthenticated
############## Main Installation  ####################
RUN apt-get update && apt-get install ${APT_OPTS} \
    ${BUILD_DEP}

# Clone DASHC
RUN git clone --depth=1 https://github.com/uccmisl/dashc.git

### This section copies the steps done in configure from https://github.com/uccmisl/dashc.git ###
# Install opam
RUN wget https://raw.githubusercontent.com/ocaml/opam/master/shell/install.sh

### Hack to avoid prompt for directory
RUN sed -i 's/read BINDIR/BINDIR="$DEFAULT_BINDIR"/g' install.sh
RUN sh ./install.sh
#disable sandboxing needed for docker
RUN opam init --auto-setup --comp 4.07.1 --yes --disable-sandboxing

WORKDIR /dashc
## Install requirements (from configure)
RUN eval $(opam env) && \
    opam install -y async_ssl dune core async xml-light alcotest alcotest-async merlin ocp-indent utop cohttp 'cohttp-async<2.1.1' 'base64<3.0.0'

RUN git clone https://github.com/mirage/ocaml-cohttp.git && \
    cd ocaml-cohttp && \
    git checkout 13f4bd609e9153b3d92acfddd1e257996e8a4a91

RUN rm ocaml-cohttp/cohttp-async/src/client.ml && \
    rm ocaml-cohttp/cohttp-async/src/client.mli && \
    cp ocaml-cohttp_/cohttp-async/src/client.ml ocaml-cohttp/cohttp-async/src/client.ml

RUN eval $(opam env) && \
    opam remove -y cohttp cohttp-async && \
    opam pin add -y cohttp ocaml-cohttp && \
    opam pin add -y cohttp-async ocaml-cohttp

# Build dashc.exe
RUN eval $(opam config env) && make

###################### End Build stage ##################################

###################### Final stage ######################################
# Here we make our "normal" image
FROM monroe/base

MAINTAINER jonas.karlsson@kau.se

ENV APT_OPTS -y --allow-downgrades --allow-remove-essential --allow-change-held-packages --allow-unauthenticated

############## Main Installation  ####################
RUN apt-get update && apt-get install ${APT_OPTS} \
    libssl1.0.2 \
    libffi6 \
    python-dev gcc && \
    pip install "flatten_json==0.1.7" subprocess32 && \
    apt-get purge -y python-dev gcc && \
    apt-get clean && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*


#Copy only the relevant parts from the build stage
COPY --from=build /dashc/dashc.exe /usr/local/bin/

# This is the experiment that should run once the container is started
COPY files/* /opt/monroe/

ENTRYPOINT ["dumb-init", "--", "/usr/bin/python", "/opt/monroe/experiment.py"]
