#!/bin/bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

CONFIG_FILE=$SCRIPTPATH/../src/braid_db/funcx/endpoint_config.py
VENV_PATH=$SCRIPTPATH/../.venv
ACTIVATE_SCRIPT=$VENV_PATH/bin/activate

funcx_endpoint_name=${1:-braid_db}

echo Configuring endpoint $funcx_endpoint_name

# create temporary file
tmpfile=$(mktemp /tmp/braid-db.XXXXXX)

# create file descriptor 3 for writing to a temporary file so that
# echo ... >&3 writes to that file
exec 3>"$tmpfile"

# create file descriptor 4 for reading from the same file so that
# the file seek positions for reading and writing can be different
exec 4<"$tmpfile"

echo "venv_activate='$ACTIVATE_SCRIPT'" >&3

cat $CONFIG_FILE 1>&3

echo config file

cat <&4

echo end of config file

echo funcx-endpoint configure --endpoint-config "$tmpfile" "$funcx_endpoint_name"
funcx-endpoint configure --endpoint-config "$tmpfile" "$funcx_endpoint_name"

# delete temp file; the directory entry is deleted at once; the reference counter
# of the inode is decremented only after the file descriptor has been closed.
# The file content blocks are deallocated (this is the real deletion) when the
# reference counter drops to zero.
rm "$tmpfile"
