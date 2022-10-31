.. Braid-DB documentation master file, created by
   sphinx-quickstart on Mon Oct 24 14:32:07 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Braid-DB's documentation!
====================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Overview
========

* Embrace automation in data analysis, retention, decision-making
* Enable users to trace back to how decisions were made
* Necessitates recording what went into model training, including external data, simulations, and structures of other learning and analysis activity
* Envision a versioned database for ML model states with HPC interfaces
* Develop recursive and versioned provenance structures:
   * Models may be constructed via other models (estimates, surrogates)
   * Models are constantly updated (track past decisions and allow updates)
* Integrate with other Braid components

== Architecture

:imagesdir: https://github.com/ANL-Braid/DB/raw/main/img

=== Conceptual architecture

image::conceptual-architecture.png[]

=== Software block diagram

image::block-diagram.png[]

== Use cases

=== SLAC workflow

==== Goals

. Perform data reduction at the edge
. Train models on specific characteristics of experiment-specific data

==== Workflow

. Scientist configures experiment parameters
. Workflow launches simulations with experiment parameters
. Complete simulations by time experiment data collection is complete
. Train model on simulation and experiment data
. Run model on an FPGA to perform data reduction in production

==== Provenance records

===== Notes

* Everything has typical metadata like timestamps
* Records can be updated
** Not immutable history like most provenance data
** Old versions can be recovered and used

===== Records

. Experimental configurations (independent?)
. Experiment outputs
. Other simulation inputs?
.. Software version, configuration?
. Simulation outputs
. Training data ingest
. Inference outputs (statements)
.. Could be in the form of tests
.. Like a super-Jenkins

=== BraggNN workflow

==== Goals

. Improve peak finding
. Train model to represent Bragg peaks

==== Workflow

. Scientist configures experiment parameters
. APS collects raw scattering data
. Run peak finding on raw data, label peaks
. Train model on peaks to represent raw data
. Reproduce and save peak locations

==== Provenance records

===== Notes

* Everything has typical metadata like timestamps

===== Records

. Experimental configurations (independent?)
. Experiment outputs
. Derived peak locations
. Models trained, checkpoints, etc.
. Inferred peak locations from trained model

=== SSX

==== Goals

. Track the provenance of SSX crystal structures

==== Workflow

. Scientists create a beamline.json and process.phil file
. Analysis is performed on the input data using these configs to create int files
. The int files are used with a prime.phil file to create a structure

==== Provenance records

===== Notes

. Structures can come from multiple experiments. This is defined by an intlist in the prime.phil file.

===== Records

. Experimental config files (phil, beamline.json)
. Analysis results (int files)
. Derived structure

=== CTSegNet

==== Goals

. Track the history of various U-Net-like models used for trial-and-error image segmentation

==== Workflow

https://raw.githubusercontent.com/aniketkt/CTSegNet/master/notebooks/CTSegNet_continuouslearning.png[Diagram]

. A tomo scan is obtained
. Perform image processing, contrast adjustment, etc.
. Apply (labeling) "masks"
. Run ensemble models in inference mode
. Get new segmentations
. Aggregate segmentation results
. Re-train models and loop...

==== Provenance notes

. Models are trained on inferences of previous models
. Provenance queries:
.. "What data was used to train this model?"
. Refer to TomoBank IDs for data identification scheme
. Need rich metadata for search

=== Samarakoon/Osborn

==== Goals

. Fit simulated crystal structure to scattering data

==== Workflow

. Obtain neutron scattering data
. Apply auto-encoder to identify important features
. Apply dimensionality reduction
. Fit to data

== Getting started

Note: Additional docs forthcoming to help get setup in a (mini)conda based environment.

* Start by installing poetry via pip or
https://python-poetry.org/docs/#osx--linux--bashonwindows-install-instructions

* Then, run `poetry install` to setup a local virtual environment from which to run other applications
* Run, `poetry run pre-commit install` to setup pre-commit hooks for code formatting, lining, etc.
* Tests can be run using scripts in the `test` directory.
* Unit tests can be run with the command `poetry run pytest pytests/` which will run the pytest test driver from the current virtual environment on all then tests defined in the `pytests` directory.

Working with FuncX
==================

Setup
-----

. `pip install funcx funcx-endpoint`


Usage
-----

Using FuncX requires that the `funcx-endpoint` be installed in a working environment whether it is a conda, pip or otherwise installed process.

Setting up to run with funcx is a multi-step process:

1. Create a new funcX endpoint configured so that it can use the BraidDB library. This can be done with the shell script: `scripts/configure_funcx_endpoint.sh`. Provide one command line argument: the name of the funcx endpoint to be created/configured. If no name is provided, the endpoint will be named `braid_db`. This endpoint will be configured such that it has access to the implementation stored in the `.venv` directory of the braid db project.

2. Start the new endpoint with the command `funcx-endpoint start <endpoint_name>` where `endpoint_name` is as configured in the previous step. Take note of the UUID generated for the new endpoint.

3. If you want the funcx hosted braid db to store files in a different location, edit `src/braid_db/funcx/funcx_main.py` and change the value of `DB_FILE` in the function `funcx_add_record`. If not edited the funcx-based operations will store their entries in the file `~/funcx-braid.db`.

4. Register the function(s) to be exposed to funcx. This can be done with the command `.venv/bin/register-funcx` (or `poetry run register-funcx`). Note that this requires that the command `poetry install` has previously been run so that the script is installed in the virtual environment (in the `.venv/bin` directory). This will register a number of functions printing the name of the function and the funcx uuid for the registered function.

The functions are:
  * `add_record_for_action_step`: This simply adds a record to the DB which is commonly used to represent a step of a Globus Flow having been run.
  * `add_transfer_request`: This is a helper for adding a record to the DB representing a Globus Flow step using the Globus Transfer Service. It will also create records for the source and destination of the Transfer with dependency from the source, to the workflow step to the destination.
  * `create_invalidation_action`: Creates an invalidation action in the DB. It takes as input the operations to perform when an invalidation should occur.
  * `add_invalidation_action_to_record`: Creates an association between a record in the DB and an invalidation action (most likely created with the `create_invalidation_action` function above.

The various functions return output in a format which places state into a running Globus Flow which can be consumed by subsequent steps which invoke other functions. For example, the `add_record_for_action_state` function returns the DB record id in its output. Subsequent calls to this function within a Flow can reference this output as a "predecessor" and the function will interpret the input such that it can determine the previous step's record id and create the dependency between the newly created record and the previous record.


5. *Deprecated at this time* To test invoking the add record function via funcx, run the command: `.venv/bin/funcx-add-record --endpoint-id <endpoint_id> --function-id <function_id>` using the value for endpoint id and function id output in the previous steps. This should output the record id. One can use a tool like `sqlite3` to verify that records are stored in the database file.  *Deprecated at this time*

Developer notes
===============

* There is a high-level SQL API wrapper in db_tools called BraidSQL. +
  This API is generic SQL, it does not know about Braid concepts
* The high-level Braid Database API is called BraidDB
* BraidDB is used by the Braid concepts: BraidFact, BraidRecord,
  BraidModel, ...
* The Braid concepts are used by the workflows
* We constantly check the DB connection because this is useful when
  running workflows

Tools
=====

bin/braid-db-create::
Creates a DB based on the structure in braid-db.sql

bin/braid-db-print::
Print the DB to text

Tests
=====

Tests are in the test/ directory.

Tests are run nightly at:

* https://jenkins-ci.cels.anl.gov/job/Braid-DB-Core
* https://jenkins-ci.cels.anl.gov/job/Braid-DB-Workflows

They are also run via Github Actions for each push or pull request against the origin repo.




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
