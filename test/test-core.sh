#!/bin/bash
set -eu

# TEST CORE SH

THIS=$(  readlink --canonicalize $( dirname $0 ) )
BRAID=$( readlink --canonicalize $THIS/.. )

echo
echo "TEST-CORE ..."

(
  set -x
  pwd
  cd $BRAID/test

  DB=braid.db
  if [[ -e $DB ]]
  then
    mv --verbose --backup=numbered $DB $DB.bak
  fi

  ./test.sh test-0.py
  ./test.sh test-1.py
)

echo "TEST-CORE: OK."
echo
