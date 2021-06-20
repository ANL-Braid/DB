#!/bin/zsh -f
set -eu

PROCS=1
zparseopts -D -E n:=N
if (( ${#N} )) {
  PROCS=${N[2]}
}

CYCLES=100
EXPERIMENT_COUNTS=( {10..100..10} )
MODEL_COUNTS=(      {10..100..10} )
TRIALS=( {1..5} )

typeset -Z 3 EXPERIMENTS MODELS

cursor_line_reset()
{
  cursor_line_start
  cursor_line_erase
}

cursor_line_start()
{
  local e='\033['
  printf "${e}70D"
}

cursor_line_erase()
{
  local e='\033['
  printf "${e}K"
}

foreach EXPERIMENTS in $EXPERIMENT_COUNTS
do
  EXPERIMENTS=$(( EXPERIMENTS / PROCS ))
  foreach MODELS in $MODEL_COUNTS
  do
    DATA=mascot-$EXPERIMENTS-$MODELS.data
    print "Running: $DATA"
    LOGS=()
    for TRIAL in $TRIALS
    do
      printf "TRIAL=$TRIAL"
      LOG=mascot-$EXPERIMENTS-$MODELS-$TRIAL.log
      # echo -ne > $LOG  # Truncate log
      A=( --experiments $EXPERIMENTS
          --models $MODELS
          --configurations $MODELS )
      if [[ -f braid-mascot.db ]] rm braid-mascot.db
      ./workflow.sh -- $A --time > $LOG
      LOGS+=$LOG
      cursor_line_reset
    done
    printf "$A  " > $DATA
    awk -f avg-rates.awk $LOGS >> $DATA
  done
done
