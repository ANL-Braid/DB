#!/bin/bash
set -eu

# TEST WORKFLOWS SH

THIS=$(  readlink --canonicalize $( dirname $0 ) )
BRAID=$( readlink --canonicalize $THIS/.. )

echo
echo "TEST-WORKFLOWS ..."

for WORKFLOW in SLAC BraggNN
do
  echo
  echo "TEST WORKFLOW: $WORKFLOW ..."
  (
    set -x
    pwd
    $BRAID/workflows/$WORKFLOW/workflow.sh
  )
  echo "TEST WORKFLOW: $WORKFLOW OK."
done

echo
echo "TEST-WORKFLOWS: OK."
echo
