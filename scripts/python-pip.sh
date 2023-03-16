# python 3.8.0
sudo apt update
sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev \
libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev
wget https://www.python.org/ftp/python/3.8.0/Python-3.8.0.tgz
tar -xf Python-3.8.0.tgz
cd Python-3.8.0
./configure --enable-optimizations
make -j$(nproc)
sudo make altinstall
python3.8 --version

# remove old links
sudo rm -rf /usr/bin/python3.5
sudo rm -rf /usr/bin/python3.5m
sudo rm -rf /usr/lib/python3.5
sudo rm -rf /etc/python3.5
sudo rm -rf /usr/local/lib/python3.5

# pip
cd ../
wget https://bootstrap.pypa.io/get-pip.py
python3.8 get-pip.py