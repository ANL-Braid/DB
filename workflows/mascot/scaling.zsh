#!/bin/zsh -f
set -eu

EXPERIMENTS=10
MODELS=10
TRIALS=( 1   ) # {1..5} )

THIS=$(  readlink --canonicalize $( dirname $0 ) )
BRAID_HOME=$( readlink --canonicalize $THIS/../.. )
export BRAID_HOME
export PYTHONPATH=$BRAID_HOME/src

typeset -Z 3 PROCS

foreach PROCS in 24 # 16 # 8  # 3 4 6 8 # 12 16 24
do
  DB=braid-mascot-$PROCS.db
  [[ -f $DB ]] && rm -v $DB
  $BRAID_HOME/bin/braid-db-create -B $DB
  DATA=mascot-scaling-$PROCS.data
  print "Running: $DATA"
  # echo -ne > $LOG  # Truncate log
  LOGS=()
  for TRIAL in $TRIALS
  do
    for RANK in {1..$PROCS}
    do
      LOG=mascot-scaling-$PROCS-$TRIAL-$RANK.log
      A=( --experiments $(( $EXPERIMENTS / $PROCS ))
          --models $MODELS
          --configurations $MODELS
          --db $DB
        )
      LOGS+=$LOG
      {
        print "FLAGS: $A PROCS=$PROCS"
        python3 workflow.py $A --time --verbose 2
        printf "\n\n"
      } >& $LOG &
    done
    wait
    echo CODE $?
  done
  printf "$A  " > $DATA
  awk -f avg-rates.awk $LOGS >> $DATA
done
