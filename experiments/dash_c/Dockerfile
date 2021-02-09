
###################### Build stage ######################################
# Here we build dash_c
FROM ubuntu:18.04 AS build

MAINTAINER jonas.karlsson@kau.se
#ENV BUILD_DEP="libffi-dev git libssl-dev"
#From configure in https://github.com/uccmisl/dashc.git
ENV BUILD_DEP="bubblewrap m4 git python3-pip net-tools wget mercurial darcs libcap-dev unzip sed pkg-config libffi-dev libssl-dev"
ENV DEBIAN_FRONTEND=noninteractive
ENV APT_OPTS -y --allow-downgrades --allow-remove-essential --allow-change-held-packages --allow-unauthenticated

############## Main Installation  ####################
RUN apt-get update && apt-get install ${APT_OPTS} \
    ${BUILD_DEP}

#Clone DASH C
RUN git clone --depth=1 https://github.com/uccmisl/dashc.git

###From configure in https://github.com/uccmisl/dashc.git###
# Install opam
RUN wget https://raw.githubusercontent.com/ocaml/opam/master/shell/install.sh
RUN sed -i 's/read BINDIR/BINDIR="$DEFAULT_BINDIR"/g' install.sh
RUN sh ./install.sh
RUN opam init --auto-setup --comp 4.07.1 --yes --disable-sandboxing

WORKDIR /dashc
# Install requirements
RUN pip3 install numpy
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
    libffi6 && \
    apt-get clean && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

Copy only the relevant parts from the build stage
COPY --from=build /dashc/dashc.exe /opt/monroe/

# This is the experiment that should run once the container is started
COPY files/experiment.py /opt/monroe/

ENTRYPOINT ["dumb-init", "--", "/usr/bin/python", "/opt/monroe/experiment.py"]
