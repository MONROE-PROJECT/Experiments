# Monroe Virtual Node
The virtual node emulates a mobile MONROE node with 3 mobile interfaces + eth0 and wifi
(op0 op1 op2 eth0 wlan0).
The purpose of the virtual node is as a first stage testing environment to
adapt scripts etc. to the metadata format and interface naming scheme.

The virtual node will replay a metadata stream from a real node (with updated
timestamps). The original metadata stream can be found in
metadata-publisher/files/metadata.dump    

The purpose of the virtual node is not to fully emulate a mobile node and
all network conditions in such a environment.
There is therefore no mapping between the values reported in the metadata stream and
the actual network conditions (rtt, packet loss etc.). In the virtual node all
interfaces are directly mapped to the docker bridge (ie wired) interface.

## Requirments
* Windows and Linux [VMWare Player (Free)](https://my.vmware.com/en/web/vmware/free)
* MAC [VMWare Fusion (30 day trail)](http://www.vmware.com/products/fusion.html)
* Untested alterntive [Docker Toolbox](https://www.docker.com/products/docker-toolbox)

## Usage
1. Clone this repository (git clone https://github.com/MONROE-PROJECT/Experiments.git)
2. In vmplayer or fusion open MONROE-VirtualNode.vmx (File->Open a Virtual Machine)
and launch it (make sure shared folders are enabled).
3. When the virtual machine has booted up do:
    1. cd /mnt/hgfs/host/
    2. ./run-virtualnode.sh
4. To run and test you container do :
    1. ./run-container.sh <container> <optional docker commandline options>
        eg. ./run-container.sh monroe/base "-ti --entrypoint bash"

### Alternative if using Docker Toolbox (untested but could/should work)
The MONROE virtual node and docker toolbox are both based on [boot2docker](http://boot2docker.io/).
Therefore, it should be possible to run the virtual node without vmplayer or fusion.
Caveate: The script run-virtualnode.sh will alter the network configuration inside the
docker toolbox in a non trivial way so be warned.

Steps to run in docker toolbox (untested):
1. Start/Boot into Docker Toolbox.
2. Clone this repository (git clone https://github.com/MONROE-PROJECT/Experiments.git)
3. cd Experiments/virtualnode
4. ./run-virtualnode.sh
5. To run and test you container do (might need to modify docker mount point /mnt/hgfs/host/results/):
    1. ./run-container.sh <container> <optional docker commandline options>
        eg. ./run-container.sh monroe/base "-ti --entrypoint bash"


## Technical description

The script run-virtualnode.sh will build a metadata replayer container and
setup the routing via the script scripts/net-config.sh

Basically this is done to let the environment look like a real node ie:
  * the container runs in this separate network namespace (netns monroe).
  * any interface available in the host network namespace will be mapped into the container network namespace.
  * a veth bridge interface called "metadata" is created inside the monroe network namespace. This allows to connect to the metadata broadcast using the address tcp://172.17.0.1:5556
  * a storage directory is mapped to /monroe/results inside the container.

The script run-container.sh will launch the specified container (and pull it first if it does not exist locally) in the correct network namespace with the folder results mapped insdide the container (to /monroe/results).
