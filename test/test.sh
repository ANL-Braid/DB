#!/bin/bash
set -eu

THIS=$( readlink --canonicalize $( dirname $0 ) )
BRAID=$( readlink --canonicalize $THIS/.. )

if (( ${#} < 1 ))
then
  echo "test.sh: Provide a test!"
  exit 1
fi
TEST=$1
shift

export PYTHONPATH=${PYTHONPATH:-}:$BRAID/src
python $THIS/$TEST ${*}
# Returns exit code from python
