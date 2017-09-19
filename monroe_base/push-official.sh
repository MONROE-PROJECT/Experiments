#/bin/sh
TODAY=$(date +"%y%m%d")
docker tag monore/base:staging monore/base
docker login && docker push monroe/base && echo "Pushed official monroe/base:latest"
docker tag monore/base monore/base:${TODAY}
docker push monore/base:${TODAY} && echo "Pushed official monroe/base:${TODAY}"
