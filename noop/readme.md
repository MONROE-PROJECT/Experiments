# Monroe noop

A noop container based on monore/base. Only used to create the correct NetworkNamespace

# How to update
  1. Login docker hub ```docker login```
  2. Build the image ```docker build -f noop.docker -t noop .```
  3. Tag the image ```docker tag noop monroe/noop```
  4. Push it to the repo ```docker push monroe/noop```
  or ./build.sh && ./push.sh
