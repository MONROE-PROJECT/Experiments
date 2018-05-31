# Experiment to showcase the virtual machine support in the monroe platform 
The purpose of this experiment is to output a log of the configuration and results of connectivity tests when run either as a virtual machine or as a docker container.

The experiment can run both as a virtual machine (by specifing ```"vm":1``` as a parameter when scheduling the experiment) or as a a normal experiment by not specifinyng any parameter. 

## Caveat:
Due to the installation of the debian default kernel the experiment container is rather large (ie 200MB). It is prefferable to only run this experiment on ethernet connected nodes. 

