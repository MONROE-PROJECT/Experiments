
curl -o bind.tar.gz "https://www.isc.org/downloads/file/bind-9-11-2/?version=tar-gz"
tar zxvf bind.tar.gz
cd bind-9.11.2
apt-get update && apt.get intall libjson-c-dev libssl-dev
./configure --with-openssl --with-libjson
make 
# dig is located in bin/dig/dig
