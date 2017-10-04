#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

image=${DIR##*/}

filesystem_image="image.tar"
disk_image="image.qcow2"
# We make the disk_image 500 MB larger than necessary
# Will be allocated on demand
disk_size="+500M"

if [ ! -f $disk_image ]; then
  echo "$(date): Rebuilding the image"
  docker pull $(awk '/FROM/{ print $2 }' Dockerfile)
  docker build --rm --no-cache -t ${image} . \
  && echo "Finished building ${image}"

  echo "$(date): Running a container from '${image}' image"
  container_id=$(docker run -d ${image} ls)

  echo "$(date): Exporting image content to a tar archive"
  docker export ${container_id} > ${filesystem_image}

  echo "$(date): Creating new QCOW2 disk image"
  virt-make-fs \
  --size=${disk_size} \
  --format=qcow2 \
  --type=ext4 \
  --partition -- ${filesystem_image} ${disk_image}

  echo "$(date): Deleting intermediate image"
  rm -f $filesystem_image

  echo "$(date): Modyfying the image with guestfs"
  guestfish -x <<EOF
add ${disk_image}
run
mount /dev/sda1 /
sh "/usr/sbin/update-initramfs -u"
sh "/usr/sbin/grub-install --recheck --no-floppy /dev/sda"
sh "/usr/sbin/grub-mkconfig -o /boot/grub/grub.cfg"
EOF
fi

echo "$(date): You can run the image with this command: \
      'kvm -m 1048 -hda $disk_image'"
