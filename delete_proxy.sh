#!/bin/bash

if [ $# -ne 1 ]; then
    echo "No argument provided"
    exit 1
fi

FILE="/etc/3proxy/.proxyauth"

UUID="$1"

if [ ! -f "$FILE" ]; then
    echo "File '$FILE' does not exist"
    chmod 400 $FILE
    exit 1
fi

chmod 640 $FILE

TMP_FILE=$(mktemp)

grep -v "^${UUID}:" "$FILE" > "$TMP_FILE"

if cmp -s "$FILE" "$TMP_FILE"; then
    echo "Client UUID '$UUID' not found in file '$FILE'"
    rm "$TMP_FILE"
    chmod 400 $FILE
    exit 0
fi

mv "$TMP_FILE" "$FILE"
rm "$TMP_FILE"

echo "Clien UUID '$UUID' deleted from file '$FILE', restarting 3proxy..."

chmod 400 $FILE

sudo systemctl daemon-reload
sudo systemctl restart 3proxy

echo "Client deleted from $output_file"

