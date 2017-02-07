# Tunnelbox-server
This container acts as a ssh reverese tunnel endpoint where clients can directly connect to their experiment containers (on any monroe node).
The purpose is to allow experimenters a interactive way of accessing a experiment running on a real monroe node during development or debugging.
The server parses a url for public keys of containers that should be allowed to establish a reverse ssh tunnel according to the below scheme:
1. Scheduler exposes public keys of the containers that should connect in https://scheduler.monroe-system.eu/v1/backend/pubkeys
2. The script regulary parse these keys and insert them authorized keys
3. and the container can now establish the tunnel connection.

The client supplies its own public ssh key to the the experiment container and
uses that together with instructions (port and host information) provided by the web interface (of the scheduler)
to connect to its experiment container.

# Docker
The container requires that docker is installed and working.
The container uses (default) ports between 29999-31000. The first port is used by the server, the remaining are for client nodes (NODEID + 30000)
docker options : --restart=always -p 29999-31000:29999-31000
