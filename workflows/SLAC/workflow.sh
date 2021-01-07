#!/bin/bash
set -eu

# SLAC WORKFLOW

echo
echo "WORKFLOW SLAC ..."

THIS=$(  readlink --canonicalize $( dirname $0 ) )
BRAID=$( readlink --canonicalize $THIS/../.. )

export PYTHONPATH=$BRAID/src

cd $BRAID/workflows/SLAC

python workflow.py $*
