#!/bin/bash
set -eu

# SETUP SH
# See README.adoc

which pip

echo "setup.sh: confirm?"
read _

(
  set -x
  pip install poetry sphinx
  poetry install
)

echo "setup.sh: OK"
