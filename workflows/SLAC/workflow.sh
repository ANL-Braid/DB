#!/bin/bash
set -eu

# SLAC WORKFLOW

echo
echo "WORKFLOW SLAC ..."

THIS=$(  readlink --canonicalize $( dirname $0 ) )
BRAID_HOME=$( readlink --canonicalize $THIS/../.. )
export BRAID_HOME

export PYTHONPATH=$BRAID_HOME/src

cd $BRAID_HOME/workflows/SLAC

python3 workflow.py $*
