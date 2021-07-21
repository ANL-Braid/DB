#!/bin/zsh
set -eu

zparseopts -D -E n:=PROCS
if (( ! ${#PROCS} )) {
  PROCS=( -n 2 )
}

# set -x
THIS=$(  readlink --canonicalize $( dirname $0 ) )
BRAID=$( readlink --canonicalize $THIS/.. )

export PYTHONPATH=${PYTHONPATH:-}:$BRAID/src

mpiexec $PROCS python -u $THIS/test_mpi_check.py
