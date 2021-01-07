#!/bin/bash
set -eu

# BraggNN WORKFLOW

echo
echo "WORKFLOW BraggNN ..."

THIS=$(       readlink --canonicalize $( dirname $0 ) )
BRAID_HOME=$( readlink --canonicalize $THIS/../.. )
export BRAID_HOME

export PYTHONPATH=$BRAID_HOME/src

cd $BRAID_HOME/workflows/BraggNN

python workflow.py $*
