
# AVG TIMES AWK
# Report the average of the "mascot time:" lines

BEGIN {
  sum = 0
  count = 0
}

$1 == "mascot" && $2 == "time:" { sum += $3; count += 1; }

END {
  print sum/count;
}
