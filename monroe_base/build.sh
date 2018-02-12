#/bin/sh
LEVEL=$1

NAME=monroe/base
FINALTAG=complete
DEFAULTTAG=cli
OLDTAG=old
LASTTAG=$(ls *_docker|tail -n1|cut -f2 -d"_")

LEVELS=$(ls *_docker | cut -f1 -d"_")

# Retag the old default and remove the old tag
# This is safe even if we do not rebuild the default 
docker pull ${NAME} 
docker tag ${NAME} ${NAME}:${OLDTAG}
docker rmi ${NAME}



# Find out which level 
if [[ ! ${LEVELS[*]} =~ "${LEVEL}" ]]
then
    echo "First argument must be on of the following:"
    echo "${LEVELS[*]}"
    exit 1
fi

for l in ${LEVELS[*]}
do
    dockerfile="$(ls ${l}_*_docker)"
    tag="$(echo ${dockerfile}|cut -f2 -d"_")"
    CONTAINER=${NAME}:${tag}
    if [[ $l -ge $LEVEL ]]
    then
	echo "Building $tag"
        if [ "$tag" == "core" ]
        then
            TMPNAME="${CONTAINER}_tmp"
            docker pull $(awk '/FROM/{ print $2 }' ${dockerfile})
            docker build --rm --no-cache -f ${dockerfile} -t ${TMPNAME} . && \
            ID=$(docker run -d ${TMPNAME} /bin/bash) && \
            docker export ${ID} | docker import - ${CONTAINER} && \
            docker rm -f ${ID} && docker rmi -f ${TMPNAME} && \
            echo "Finished building ${CONTAINER}" || exit 1
        else
            docker build --rm --no-cache  -t ${CONTAINER} -f ${dockerfile} . && \
            echo "Finished building ${CONTAINER}" || exit 1
        fi
    else
        docker pull ${CONTAINER} || exit 1
    fi
done
# Hard code which version that will be the "default" if no tag is given
docker tag ${NAME}:${DEFAULTTAG} ${NAME}

# Automatcially set the top "tag" to
docker tag ${NAME}:${LASTTAG} ${NAME}:${FINALTAG}
