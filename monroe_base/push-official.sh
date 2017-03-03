#/bin/sh
TODAY=$(date +"%y%m%d")
docker tag monore/base:staging monore/base
docker tag monore/base:staging monore/base:${TODAY}
docker login && docker push monroe/base && echo "Pushed official monroe/base:{TODAY}"
