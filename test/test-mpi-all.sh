#!/bin/bash
set -eu

# TEST MPI ALL
# For Jenkins or interactive use

THIS=$(  readlink --canonicalize $( dirname $0 ) )

$THIS/test-mpi-01.sh
