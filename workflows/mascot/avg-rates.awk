
# AVG RATES AWK
# Report the average of the "mascot rate:" lines

BEGIN {
  sum   = 0
  count = 0
}

$1 == "mascot" && $2 == "size:" { size = $3; }
$1 == "mascot" && $2 == "rate:" { sum += $3; count += 1; }

END {
  print size, sum/count;
}
