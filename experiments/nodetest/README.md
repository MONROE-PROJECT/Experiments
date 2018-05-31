# A virtual machine show case 
The purpose of this experiment is to show case the virtual machine support in the monroe platform. 
The output of the experiment is a log of the configuration and various connectivity tests.

The experiment can run either as a virtual machine, by setting ```"vm":1``` as a parameter when scheduling the experiment, or as a normal experiment by not setting any parameter. 

## Caveat:
Due to the installation of the debian default kernel the experiment container is rather large (ie 200MB). It is, therefore, preferable to only run this experiment on ethernet connected nodes. 

