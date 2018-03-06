#!/bin/sh
echo "Setting up routing"
bash /opt/monroe/setup-routing.sh
echo "Mounting files and directories"
bash /opt/monroe/setup-mounts.sh
echo "Running User Experiment"
bash /opt/monroe/user-experiment.sh
echo "Done"
