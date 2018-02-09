build (inside container) 
curl -O http://www.ryde.net/code/bind.c.txt
mv bind.c.txt bind.c
apt-get update && apt-get install gcc
gcc -nostartfiles -fpic -shared bind.c -o bind.so -ldl -D_GNU_SOURCE
