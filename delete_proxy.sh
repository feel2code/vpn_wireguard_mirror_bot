#!/bin/bash

if [ $# -ne 1 ]; then
    echo "No argument provided" >&2
    exit 1
fi

FILE="/etc/3proxy/.proxyauth"

UUID="$1"

if [ ! -f "$FILE" ]; then
    chmod 400 $FILE
    echo "File '$FILE' does not exist" >&2
    exit 1
fi

chmod 640 $FILE

TMP_FILE=$(mktemp)

grep -v "^${UUID}:" "$FILE" > "$TMP_FILE"

if cmp -s "$FILE" "$TMP_FILE"; then
    rm "$TMP_FILE"
    chmod 400 $FILE
    echo "Client UUID '$UUID' not found in file '$FILE'" >&2
    exit 1
fi

mv "$TMP_FILE" "$FILE"
rm "$TMP_FILE"

echo "Client UUID '$UUID' deleted from file '$FILE', restarting 3proxy..."

chmod 400 $FILE
chown proxy3:proxy3 $FILE

sudo systemctl daemon-reload
sudo systemctl restart 3proxy

echo "Client deleted from $output_file"
exit 0

