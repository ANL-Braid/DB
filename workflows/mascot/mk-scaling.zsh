#!/bin/zsh -f

DATA=( mascot-scaling-*.data )
print "DATA: ${#DATA}"
awk '{ print $7, $8 }' $DATA | sort -n > inserts.data

set -x
jwplot inserts.{eps,cfg,data}
