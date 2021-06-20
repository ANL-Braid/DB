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

foreach EXPERIMENTS in $EXPERIMENT_COUNTS
do
  EXPERIMENTS=$(( EXPERIMENTS / PROCS ))
  foreach MODELS in $MODEL_COUNTS
  do
    DATA=mascot-$EXPERIMENTS-$MODELS.data
    print "Running: $DATA"
    # echo -ne > $LOG  # Truncate log
    LOGS=()
    for TRIAL in $TRIALS
    do
      LOG=mascot-$EXPERIMENTS-$MODELS-$TRIAL.log
      A=( --experiments $EXPERIMENTS
          --models $MODELS
          --configurations $MODELS )
      {
        print "FLAGS: $A"
        ./workflow.sh -- $A --time
        printf "\n\n"
      } > $LOG
      LOGS+=$LOG
    done
    printf "$A  " > $DATA
    awk -f avg-rates.awk $LOGS >> $DATA
  done
done
