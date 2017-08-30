
# Experiment
To build and run the test enviroment these packages must be installed (besides docker):
libguestfs-tools
qemu-kvm

To compile
sudo ./build.se (guestfish requires root as it read from /boot/vmlinuz)

This will create a new docker image (from monroe/base:staging) and export the filesystem (ultimatley) a cow2 file.
Update the initramfs and install grub

TODO:
Networking is currently not working (probably needs parameters in both kvm
startup script and docker file)
