#!/bin/bash

chmod 640 /etc/3proxy/.proxyauth
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 arg1 arg2"
    exit 1
fi

arg1=$1
arg2=$2

output_file="/etc/3proxy/.proxyauth"

echo "$arg1:CL:$arg2" >> "$output_file"

chmod 400 /etc/3proxy/.proxyauth

sudo systemctl daemon-reload
sudo systemctl restart 3proxy

echo "Client configured in $output_file"
