# Monroe base container for internal experiments

## Network setup

Please take a look at the file MONROE-Scheduler / files / usr / bin / container-start.sh
([recent version](https://github.com/MONROE-PROJECT/Scheduler/blob/master/files/usr/bin/container-start.sh))
to get an idea of the setup the container will run in. Please test this setup extensively.

Most notably

  * the container runs with --net=none by default (no host interfaces are visible in the container network namespace)
  * any interface that is booked via the scheduler will be mapped into the container network namespace via macvlan
  * quotas (as booked via the scheduler) are applied to the ingoing and outgoing traffic on all interfaces
  * a storage directory is mapped to /monroe/results/ inside the container. This will have a restricted size (~1GB?).

## Requirements

These directories must exist and be writable by the user/process running :    
/monroe/results/
