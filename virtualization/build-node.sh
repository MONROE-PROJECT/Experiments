#!/bin/bash

image=monroe/base:virtualization

ram_disk_path=/tmp/vmramdisk
filesystem_image="${ram_disk_path}/image.tar"
disk_image="image.qcow2"
# We make the disk_image 100 MB larger than necessary
# Will be allocated on demand
disk_size="+100M"
max_image_size="1000"

echo "$(date): Pulling the image"
docker pull ${image}

image_size=$(docker images --format "{{.Size}}" ${image}| tr -dc '0-9.'|cut -f1 -d ".") 

if (( $image_size > $max_image_size ));then 
	echo "Too big image $image_size"
	exit 1 
fi

echo "$(date): Running a container from '${image}' image"
container_id=$(docker run -d --net=none ${image} ls)

ram_disk_size=$((image_size + 100))
echo "Creating ${ram_disk_size}Mb ramdisk in ${ram_disk_path}"
mkdir -p ${ram_disk_path}
mount -t tmpfs -o size=${ram_disk_size}m tmpfs ${ram_disk_path}
 

echo "$(date): Exporting image content to a tar archive"
#doable but slowert due to compression
#docker export ${container_id}  | gzip > ${ram_disk_path}/${filesystem_image}.gz
docker export ${container_id} > ${filesystem_image}

echo "$(date): Creating new QCOW2 disk image"
virt-make-fs \
  --size=${disk_size} \
  --format=qcow2 \
  --type=ext4 \
  --partition -- ${filesystem_image} ${disk_image}

echo "$(date): Unmounting ramdisk"
rm -f ${filesystem_image}
umount ${ram_disk_path}
sleep 3
rm -rf ${ram_disk_path}

