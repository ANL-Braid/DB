Getting Started with Development
================================

Note: Additional docs forthcoming to help get setup in a (mini)conda based environment.

1. Start by installing poetry via pip or
https://python-poetry.org/docs/#osx--linux--bashonwindows-install-instructions

2. Then, run `poetry install` to setup a local virtual environment from which to run other applications
3. Run, `poetry run pre-commit install` to setup pre-commit hooks for code formatting, lining, etc.
4. Tests can be run using scripts in the `test` directory.
5. Unit tests can be run with the command `poetry run pytest pytests/` which will run the pytest test driver from the current virtual environment on all then tests defined in the `pytests` directory.


Tests
=====

Tests are in the test/ directory.

Tests are run nightly at:

* https://jenkins-ci.cels.anl.gov/job/Braid-DB-Core
* https://jenkins-ci.cels.anl.gov/job/Braid-DB-Workflows

They are also run via Github Actions for each push or pull request against the origin repo.
