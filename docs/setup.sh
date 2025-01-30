#!/bin/bash
set -eu

# SETUP SH
# See README.adoc

which pip

echo "setup.sh: confirm?"
read _

PKGS=(
  # poetry
  furo
  sphinx
  sphinx-copybutton
  sqlmodel
  SQLAlchemy
)

(
  set -x
  # sphinx-copybutton is in requirements.txt
  pip install ${PKGS[@]}
  # poetry install
)

echo "setup.sh: OK"
