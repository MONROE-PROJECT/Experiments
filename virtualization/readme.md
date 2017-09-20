
# Experiment
To build and run the test enviroment these packages must be installed (besides
  docker):
* libguestfs-tools
* qemu-kvm

To compile
sudo ./build.se (guestfish requires root as it read from /boot/vmlinuz)

This will create a new docker image (from monroe/base) and export
the filesystem to a cow2 file. Update the initramfs and install grub

# Network setup in host
ip netns monroe ip link add link opX name macvtapX type macvtap mode bridge
sleep 2
ip netns monroe ip link set dev macvtapX up

MACaddrX=$(ip netns monroe cat /sys/class/net/macvtapX/address)
TAPNUMX=$(ip netns monroe cat /sys/class/net/macvtapX/ifindex)

exec {FDX}<>/dev/tap${TAPNUMX}
kvm -curses -m 1048 -hda image.qcow2 -device virtio-net-pci,netdev=netX,mac=${MACaddrX} -netdev tap,id=netX,fd=$FDX

ip netns monroe ip link del macvtapX

op 1 inet 172.18.21.2/24 scope global op1

14: op0   inet 172.18.1.2/24
configure interface in vm to match opX + 1

## Example :

ip netns exec monroe bash
ip link add link op1 name macvtap1 type macvtap mode bridge
ip link add link op0 name macvtap0 type macvtap mode bridge
ip link set dev macvtap0 up
ip link set dev macvtap1 up
export MACaddr0=$(cat /sys/class/net/macvtap0/address)
export MACaddr1=$(cat /sys/class/net/macvtap1/address)
export TAPNUM1=$(cat /sys/class/net/macvtap1/ifindex)
export TAPNUM0=$(cat /sys/class/net/macvtap0/ifindex)
exec {FD0}<>/dev/tap${TAPNUM0}
exec {FD1}<>/dev/tap${TAPNUM1}

kvm -curses -m 1048 -hda image.qcow2 -device virtio-net-pci,netdev=net0,mac=${MACaddr0} -netdev tap,id=net0,fd=${FD0} -device virtio-net-pci,netdev=net1,mac=${MACaddr1} -netdev tap,id=net1,fd=${FD1}

when done:
ip link del macvtap0

TODO:
routing in the virtual machine and "semi automatic IP assigmnet" via guestfish  
