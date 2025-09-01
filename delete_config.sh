#!/usr/bin/expect

set username [lindex $argv 0]

if {$username == ""} {
        puts "No client uuid!"
        exit 1
}

set temp_file "./clients.txt"

spawn sh -c "/root/./wireguard-install.sh | tee $temp_file"

expect "Option:"
send "2\n"
after 5000
send "\003"
expect eof

set fh [open $temp_file r]
set output [read $fh]
close $fh

set client_number ""
foreach line [split $output "\n"] {
    if {[string match "*$username*" $line] && [regexp {^\s*(\d+)\)} $line -> number]} {
        set client_number $number
        break
    }
}

if {$client_number != ""} {
    puts "Client is $client_number"
    after 3000
    spawn /root/./wireguard-install.sh
    expect "Option:"
    send "2\n"
    expect "Client:"
    after 3000
    send "$client_number\n"
    after 2000
    expect "Confirm"
    after 2000
    send "y\n"
    expect eof
    puts "Client $username deleted"
    file delete $temp_file
	exit 0
} else {
    puts "Client $username not found"
    file delete $temp_file
	exit 1
}

