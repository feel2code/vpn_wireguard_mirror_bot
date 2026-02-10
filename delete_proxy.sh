#!/bin/bash

if [ $# -ne 1 ]; then
    echo "No UUID (1 arg)" >&2
    exit 1
fi

FILE="/usr/local/3proxy/conf/passwd"
ORIGINAL_OWNER=$(stat -c "%U:%G" "$FILE")
UUID="$1"

chmod 640 "$FILE" || {
    echo "Cannot change file permissions in file $FILE" >&2
    exit 1
}

TMP_FILE=$(mktemp) || {
    echo "Cannot create temp file" >&2
    exit 1
}

grep -v "^${UUID}:" "$FILE" > "$TMP_FILE"

if cmp -s "$FILE" "$TMP_FILE"; then
    rm "$TMP_FILE"
    chmod 440 "$FILE"
    echo "UUID '$UUID' not found in file '$FILE'" >&2
    exit 1
fi

mv "$TMP_FILE" "$FILE"

chown "$ORIGINAL_OWNER" "$FILE"
chmod 440 "$FILE"

echo "UUID '$UUID' removed from file '$FILE', restarting 3proxy..."

systemctl restart 3proxy

echo "client '$UUID' deleted"

exit 0
