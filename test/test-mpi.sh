#!/bin/zsh
set -eu

# TEST MPI
# MPI test runner

zparseopts -D -E n:=PROCS
if (( ! ${#PROCS} )) {
  PROCS=( -n 2 )
}

if (( ${#*} == 0 )) {
  print "Provide a test!"
  exit 1
}

TEST=$1

# set -x
THIS=$(  readlink --canonicalize $( dirname $0 ) )
BRAID_HOME=$( readlink --canonicalize $THIS/.. )
export BRAID_HOME

export PYTHONPATH=${PYTHONPATH:-}:$BRAID_HOME/src

if ! [[ -f $THIS/$TEST ]] {
  print "Does not exist: TEST=$TEST"
  exit 1
}

mpiexec -l $PROCS python -u $THIS/$TEST
