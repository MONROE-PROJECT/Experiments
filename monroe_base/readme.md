# Monroe base container
Used as a base container for experiments in the Monroe project.

The container is based on debian stretch with (Monroe) common experiment tools added.

For a list of current packages installed and folders created see [dockerfile](https://github.com/MONROE-PROJECT/Experiments/blob/master/monroe_base/02_cli.docker).
Besides the installed packages the container adds these  [Utilities/Helperscripts](https://github.com/MONROE-PROJECT/Experiments/tree/master/monroe_base/core/) script/files.

Currently the only script installed are monroe_exporter.py that is a small utility to atomically save json messages in a specified directory
 (must exist and be writable).  

## Requirements

If using the monroe_exporter script the defined "results" directory must exist
and be writable (default ```/monroe/results```)   

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
