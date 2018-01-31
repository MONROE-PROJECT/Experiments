# rmbt-client - RMBT speed measurement client in C

For more information about RMBT see also:

* RMBT specification: https://www.netztest.at/doc/
* Open-RMBT: https://github.com/alladin-IT/open-rmbt
* alladin-Nettest: https://nettest.alladin.at/
* [MONROE](https://www.monroe-project.eu/) experiment nettest: https://github.com/MONROE-PROJECT/Experiments/tree/master/experiments/nettest

This code is licensed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

## Building

rmbt-client has the following requirements:

* `autoconf`, `automake`, `make`
* `gcc`, `clang` or another C compiler
* `libuuid`
* `libssl`, `libcrypto`
* `libjson-c`
* (`xz-utils` / `liblzma`)
* (`git`)

To install the required build dependencies on `apt` based distos (Debian, Ubuntu, ...) run:

```
sudo apt install libc-dev git autoconf automake make gcc pkg-config libjson-c-dev libssl-dev uuid-dev liblzma-dev
```

For `yum` based distros (CentOS, Fedora, ...) this should work:

```
yum install git autoconf automake make gcc json-c-devel openssl-devel libuuid-devel xz-devel
```

To build simply run:

```
git clone https://github.com/lwimmer/rmbt-client
cd rmbt-client
./autobuild.sh
```

To install run:
```
make install
```

## Running

To run rmbt-client you need to supply rmbt-client with the configuration.

For the most important parameters this can be done via the command line (see `rmbt -?`):

```
-c     json config file; use "-" to read from stdin
-b     local ip to bind
-h     host to connect to
-p     port to connect to
-e     connect using SSL/TLS
-t     token to use (either -t or -s is needed)
-s     secret for token generation
-f     number of flows
-d     measurement duration for downlink
-u     measurement duration for uplink
-n     number of rtt_tcp_payloads
```

Alternatively a JSON configuration file can be supplied via stdin (`rmbt -c -`) or as a file (`rmbt -c config.json`).

A minimum configuration file could look something like this:
```
{
  "cnf_server_host": "127.0.0.1",
  "cnf_server_port": 8081,
  "cnf_secret": ""
}
```

For more information see the file [`config.example.json`](config.example.json).

## Server installation

The server code can be found here: https://github.com/alladin-IT/open-rmbt

It has the following requirements:

* `make`
* `gcc`, `clang` or another C compiler
* `libssl`
* `libuuid`
* (`git`)

To install the required build dependencies on `apt` based distos (Debian, Ubuntu, ...) run:

```
sudo apt install libc-dev git make gcc libssl-dev uuid-dev
```

For `yum` based distros (CentOS, Fedora, ...) this should work:

```
yum install git make gccopenssl-devel libuuid-devel
```

To build simply run:

```
git clone https://github.com/alladin-IT/open-rmbt
cd open-rmbt/RMBTServer/
# The following line disables the token check:
sed -i 's|#define CHECK_TOKEN 1|#define CHECK_TOKEN 0|' config.h
# Generate self-signed certificate:
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -nodes -subj '/CN=localhost' -sha256 -days 10000
# Build:
make server-prod random
```

To use systemd for running rmbtd as a service you can create a file like this and save it as `/etc/systemd/system/rmbtd.service`:

```
[Unit]
Description=RMBTd
After=network.target

[Service]
WorkingDirectory=/home/rmbtd/rmbtd
ExecStart=@/home/rmbtd/rmbtd/rmbtd rmbtd -l 10080 -L 10443 -c server.crt -k server.key -u rmbtd
TimeoutStopSec=60
Restart=always

[Install]
WantedBy=multi-user.target
```

Paths and ports may need to be changed (lines given above configure to start listening on ports 10080 -without encryption- and 10443 -with encryption-).

To finally run and enable the server at bootup run the following commands as root:

```
systemctl daemon-reload
systemctl start rmbtd.service
systemctl enable rmbtdservice
```

You can use the following command (or edit the config file manually) to change the number of flows that the server allows (replace `<n>`; rebuild afterwards):
  
```
sed -i 's|#define DEFAULT_NUM_THREADS   200|#define DEFAULT_NUM_THREADS   <n>|' config.h
```
