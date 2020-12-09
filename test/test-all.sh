#!/bin/bash
set -eu

THIS=$(  readlink --canonicalize $( dirname $0 ) )
BRAID=$( readlink --canonicalize $THIS/.. )

echo
echo "TEST-ALL ..."

(
  set -x

  pwd

  cd $BRAID/test

  ./test.sh test-0.py
)

echo "TEST-ALL: OK."
echo
