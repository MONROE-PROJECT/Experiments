
# Virtualnode
The container requires that docker is installed and working.

The net-config.sh script will alter network configuration on the physical host
(ie require root or sudo).

To start the virtual node run ```./init.sh``` (root or sudo).    
After this the metadata stream is available on tcp://172.17.0.2:5556.

The metadata stream can be listened on the physcial host or inside the virtual node container.     
To login to the virtual node container run ```./login-virtualnode.sh```    

To clean up after use run ```./cleanup.sh``` (root or sudo)
