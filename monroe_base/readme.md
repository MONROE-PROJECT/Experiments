# Monroe base container/image
Used as a base container for experiments in the Monroe project.

The container is based on debian stretch with (Monroe) common experiment tools added.

For a list of current packages installed and folders created see [dockerfile](https://github.com/MONROE-PROJECT/Experiments/blob/master/monroe_base/02_cli.docker).
Besides the installed packages the container adds these  [Utilities/Helperscripts](https://github.com/MONROE-PROJECT/Experiments/tree/master/monroe_base/core/) script/files.

The container is split up on several tags. Most users should use base their experiments on monroe/base or the equivalent monroe/base:latest. We have however created two more tags for specialized experiments: 
#### Tags
* monroe/base:web --> For experiments that do chrome and firefox (headless) experiments.
* monroe/base:virt --> For experiments that should run in a virtual machine.
* monroe/base --> For all other experiments.

## Detailed description of current tags

### "Real tags"
These tags are used for defining different functionality but should normaly not be used to base experiments on 
* monroe/base:core --> common base files (based on debian:stretch), [00_core](https://github.com/MONROE-PROJECT/Experiments/tree/master/monroe_base/00_core_docker)
* monroe/base:virt --> for virtualization support (based on monroe/base:core), [01_virt](https://github.com/MONROE-PROJECT/Experiments/tree/master/monroe_base/01_virt_docker)
* monroe/base:cli --> Common tools for "command line experiments" (based on monroe/base:virt), [02_cli](https://github.com/MONROE-PROJECT/Experiments/tree/master/monroe_base/02_cli_docker)
* monroe/base:web --> Common tools for web experiments (based on monroe/base:cli), [03_web](https://github.com/MONROE-PROJECT/Experiments/tree/master/monroe_base/03_web_docker)
### "Virtual tags"
These tags point to some of the other tags and are used for convenience and backend purposes. 
* monroe/base (no tag) or monroe/base:latest --> monroe/base:cli
    * For all experiment except virtualization and web based experiments (that should use monroe/base:virt and monroe/base:web) 
* monroe/base:complete --> currently to monroe/base:web but will update as we add functinality or security patches. 
    * Used for backend purposes should not be used directly as base for any experiment.
* monroe/base:old --> The previous version of monroe/base:latest 
    * Used for backend purposes should not be used directly as base for any experiment.

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
