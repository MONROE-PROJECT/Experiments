
# Tunnelbox-server
1. Scheduler exposes public keys of the containers that should connect in https://scheduler.monroe-system.eu:4443/v1/backend/pubkeys
2. The script regulary parse these keys and insert them in the current user authorized keys
4. and the container can now establish the tunnel connection.

docker --restart=always


The container requires that docker is installed and working.
