#!/usr/bin/expect

set username [lindex $argv 0]

spawn ./wireguard-install.sh
expect "Option:"
send "1\n"
expect "Name:"
send "$username\n"
expect "DNS"
send "1\n"
expect eof
