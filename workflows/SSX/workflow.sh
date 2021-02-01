#!/bin/bash
set -eu

# SSX WORKFLOW

echo
echo "WORKFLOW SLAC ..."

THIS=$(  readlink --canonicalize $( dirname $0 ) )
BRAID_HOME=$( readlink --canonicalize $THIS/../.. )
export BRAID_HOME

# Default:
BACKUP=""

while getopts "B" OPT
do
  case $OPT in
    B) BACKUP="-B" ;;
    *) exit 1      ;;
  esac
done
shift $(( OPTIND - 1 ))

export PYTHONPATH=$BRAID_HOME/src

cd $BRAID_HOME/workflows/SSX

DB=braid-ssx.db

$BRAID_HOME/bin/braid-db-create $BACKUP $DB

python3 workflow.py $*
