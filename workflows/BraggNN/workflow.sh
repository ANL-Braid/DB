#!/bin/bash
set -eu

# BraggNN WORKFLOW

echo
echo "WORKFLOW BraggNN ..."

THIS=$(  readlink --canonicalize $( dirname $0 ) )
BRAID=$( readlink --canonicalize $THIS/../.. )

export PYTHONPATH=$BRAID/src

cd $BRAID/workflows/BraggNN

python workflow.py $*
