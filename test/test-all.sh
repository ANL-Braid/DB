#!/bin/bash
set -eu

# TEST ALL SH

THIS=$(  readlink --canonicalize $( dirname $0 ) )
BRAID=$( readlink --canonicalize $THIS/.. )

echo
echo "TEST-ALL ..."

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

echo "TEST-ALL: OK."
echo
