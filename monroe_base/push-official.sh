#/bin/sh
TODAY=$(date +"%y%m%d")
docker pull monroe/base:staging
docker tag monroe/base:staging monroe/base:${TODAY}
docker login && \
docker push monroe/base:${TODAY} && echo "Pushed official monroe/base:{TODAY}" && \
docker tag monroe/base:${TODAY} monroe/base:latest && \
docker push monroe/base && echo "Pushed official monroe/base(:latest)"
