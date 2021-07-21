#!/bin/bash
set -eu

# set -x
THIS=$(  readlink --canonicalize $( dirname $0 ) )
BRAID=$( readlink --canonicalize $THIS/.. )

export PYTHONPATH=${PYTHONPATH:-}:$BRAID/src

mpiexec -n 2 python -u $THIS/test_mpi_check.py
