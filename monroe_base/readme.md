# Monroe base container

## Network setup

Please take a look at the files [monroe-experiments](https://github.com/MONROE-PROJECT/Utilities/blob/master/monroe-experiments/usr/bin/monroe-experiments) and [container-start.sh](https://github.com/MONROE-PROJECT/Scheduler/blob/master/files/usr/bin/container-start.sh) 
to get an idea of the setup the container will run in. 

The former runs every minute to establish a network namespace for all monroe experiments.

  * the container runs in this separate network namespace (netns monroe). 
  * any interface available in the host network namespace will be mapped into the container network namespace via macvlan, using the same name. Changes in the host namespace (interfaces disappearing, appearing, going down or up) will be reflected in the monroe network namespace.
  * We currently run the [multi](https://github.com/MONROE-PROJECT/multi) DHCP client to acquire addresses and set a default route, inside the monroe network namespace. 
  * a veth bridge interface called "metadata" is created inside the monroe network namespace. This allows to connect to the metadata broadcast using the address tcp://172.17.0.1:5556
  * any parameters passed by the scheduler are available in the file /monroe/config in the form of a JSON dictionary.
  * a storage directory is mapped to /monroe/results inside the container. 

