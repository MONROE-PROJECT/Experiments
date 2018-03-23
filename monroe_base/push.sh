#/bin/sh
#TODAY=$(date +"%y%m%d")
LEVEL=$1

NAME=monroe/base
FINALTAG=complete
OLDTAG=old 
LEVELS=$(ls *_docker | cut -f1 -d"_")


# Push the final image first (as this will push all layers
echo "Pushing $FINALTAG"
docker push ${NAME}:${FINALTAG} || exit 1

# Push the old tag to preserv the previous version
echo "Pushing $OLDTAG"
docker push ${NAME}:${OLDTAG} || exit 1

if [[ ! ${LEVELS[*]} =~ "${LEVEL}" ]]
then
    echo "First argument must be one of the following:"
    echo "${LEVELS[*]}"
    exit 1
fi

for l in ${LEVELS[*]}
do
    tag="$(echo ${dockerfile}|cut -f2 -d"_")"
    patchlevel=${l:1:1}
    if [ ${patchlevel} == 0 ]; then
	    patchlevel=""
    fi
    CONTAINER=${NAME}:${tag}${patchlevel}
    if [[ $l -ge $LEVEL ]]
    then
	echo "Pushing $tag"
        docker push ${CONTAINER} && \
        echo "Finished pushing ${CONTAINER}" || exit 1
    fi
done

# Push the "default" if no tag is given
echo "Pushing default"
docker push ${NAME} || exit 1
