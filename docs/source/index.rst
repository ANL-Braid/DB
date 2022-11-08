.. Braid-DB documentation master file, created by
   sphinx-quickstart on Mon Oct 24 14:32:07 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Braid-DB's documentation!
====================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   index

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

Architecture
------------

Conceptual architecture
~~~~~~~~~~~~~~~~~~~~~~~

.. image:: https://github.com/ANL-Braid/DB/raw/main/img/conceptual-architecture.png

Software block diagram
~~~~~~~~~~~~~~~~~~~~~~

.. image:: https://github.com/ANL-Braid/DB/raw/main/img/block-diagram.png


Getting started
===============

The Braid-DB is usable as a library within other projects, or via FuncX for remote invocation from various locations. Typically, library usage will be the primary method of using Braid-DB unless there are specific requirements for accessing the Braid-DB state remotely.

Installing Braid-DB into a Python environment
---------------------------------------------

There are a variety of methods of including Python libraries into your development or run-time environment based on various tooling. We include examples for various tooling here. In all cases, the code will be pulled directly from the Braid-DB github repository as there is not, at time of writing, a method of pulling from common repositories such as PyPi. Regardless of the method of installing, the Braid-DB *requires at least Python 3.9*.

Pip
~~~

Using pip, the Braid-DB can be installed from the command line as::

    pip install git+https://github.com/ANL-Braid/DB

Alternately, deployment can be added to a `requirements.txt` file as simply::

    git+https://github.com/ANL-Braid/DB

If this line appears in a `requirements.txt` file, it can be installed via::

    pip install -r requirements.txt


Poetry
~~~~~~

Poetry is utility for installing packages in a Python development environment / virtual environment. Dependencies are specified in the `pyproject.toml` file. Braid-DB can be added to a poetry project by running the command::

    poetry add https://github.com/ANL-Braid/DB

or by adding the following to the `pyproject.toml` file::

    [tool.poetry.dependencies]
    braid-db = {git = "https://github.com/ANL-Braid/DB"}

Conda
~~~~~

Conda instructions are forthcoming.

Working with FuncX
------------------

FuncX is a remote function invocation mechanism. We provide methods for registering Braid-DB functions for creating and managing records via funcX invocations. This allows the Braid-DB to be centralized even when record creation is done in a distributed manner.

Setup and Usage
~~~~~~~~~~~~~~~

Using FuncX requires that the `funcx-endpoint` be installed in a working environment whether it is a conda, pip or otherwise installed process. For example, to install using `pip`, use the command::

    pip install funcx funcx-endpoint

Further steps involve configuring the endpoint and deploying the functions which are invoked to create and manage records.

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


Tools
=====

bin/braid-db-create::
Creates a DB based on the structure in braid-db.sql

bin/braid-db-print::
Print the DB to text

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

.. include:: use_cases.rst

.. include:: developing.rst


Troubleshooting
===============

* Python package `cryptography` may require a Rust compiler.  This could cause `poetry install` to fail while installing `cryptography`.

Site-specific Tips
==================

Summit
------

* Load module `rust/1.60.0`


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
