#!/bin/bash
set -eu

# TEST WORKFLOWS SH

THIS=$(  readlink --canonicalize $( dirname $0 ) )
BRAID=$( readlink --canonicalize $THIS/.. )
VENV_BIN=$BRAID/.venv/bin

source $VENV_BIN/activate

echo
echo "TEST-WORKFLOWS ..."

# for WORKFLOW in SSX
for WORKFLOW in SLAC BraggNN CTSegNet SSX
do
    echo poetry running workflow-$WORKFLOW
    (
        set -x
        cd $BRAID/workflows/$WORKFLOW
        $VENV_BIN/workflow-$WORKFLOW
    )
done


echo
echo "TEST-WORKFLOWS: OK."
echo
