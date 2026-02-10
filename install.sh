#!/bin/bash

apt install wget -y
wget https://github.com/3proxy/3proxy/releases/download/0.9.5/3proxy-0.9.5.x86_64.deb
dpkg -i 3proxy-0.9.5.x86_64.deb
systemctl start 3proxy
rm 3proxy-0.9.5.x86_64.deb

