
# This "experiment" show how to do a staged docker build
Staged builds are great ways to avoid installing uneccessary components (like compilers) inside a final contianer. 

This container shows two variants on how to do a staged docker build of [mptcp](github.com/multipath-tcp/mptcp).
 

## Variant 1 (self-contained)
This is the most self-contained and recommended for all projects where the build time is small.
```bash
cd self-contained
./build.sh ; # take a cup-of-coffe or three
```

## Variant 2 (eperate-containers)
The build stage in the above variant is ephemeral so when buildind a large project with only small code changes (or no chnages) the build time can be a problem.

Therefore a alternative is to use seperate containers for building and the final container. 
With this setup the build stage does not need do be redone on every "docker build". The drawback is of course that the setup becomes more complex and harder to maintanin.
To build this project first build the contianer in the "build" folder (seperate-containers/build) and then the final container (seperate-containers).