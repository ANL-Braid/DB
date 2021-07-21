#!/bin/bash
set -eu

# TEST MPI ALL
# For Jenkins or interactive use

THIS=$(  readlink --canonicalize $( dirname $0 ) )

echo "TEST MPI ALL: START ..."
echo "THIS: $THIS"
which python
python --version

$THIS/test-mpi-01.sh

echo "TEST MPI ALL: DONE."
