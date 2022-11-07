Use cases
=========

SLAC workflow
-------------

**Goals**

1. Perform data reduction at the edge
2. Train models on specific characteristics of experiment-specific data

**Workflow**

1. Scientist configures experiment parameters
2. Workflow launches simulations with experiment parameters
3. Complete simulations by time experiment data collection is complete
4. Train model on simulation and experiment data
5. Run model on an FPGA to perform data reduction in production

**Notes**

* Everything has typical metadata like timestamps
* Records can be updated
   * Not immutable history like most provenance data
   * Old versions can be recovered and used

**Records**

1. Experimental configurations (independent?)
2. Experiment outputs
3. Other simulation inputs?
   1. Software version, configuration?
4. Simulation outputs
5. Training data ingest
6. Inference outputs (statements)
   1. Could be in the form of tests
   2. Like a super-Jenkins

BraggNN workflow
----------------

**Goals**

1. Improve peak finding
2. Train model to represent Bragg peaks

**Workflow**

1. Scientist configures experiment parameters
2. APS collects raw scattering data
3. Run peak finding on raw data, label peaks
4. Train model on peaks to represent raw data
5. Reproduce and save peak locations

**Notes**

1. Everything has typical metadata like timestamps

**Records**

1. Experimental configurations (independent?)
2. Experiment outputs
3. Derived peak locations
4. Models trained, checkpoints, etc.
5. Inferred peak locations from trained model

SSX
---

**Goals**

1. Track the provenance of SSX crystal structures

**Workflow**

1. Scientists create a beamline.json and process.phil file
2. Analysis is performed on the input data using these configs to create int files
3. The int files are used with a prime.phil file to create a structure

**Notes**

1. Structures can come from multiple experiments. This is defined by an intlist in the prime.phil file.

**Records**

1. Experimental config files (phil, beamline.json)
2. Analysis results (int files)
3. Derived structure

CTSegNet
--------

**Goals**

1. Track the history of various U-Net-like models used for trial-and-error image segmentation

**Workflow**

https://raw.githubusercontent.com/aniketkt/CTSegNet/master/notebooks/CTSegNet_continuouslearning.png[Diagram]

1. A tomo scan is obtained
2. Perform image processing, contrast adjustment, etc.
3. Apply (labeling) "masks"
4. Run ensemble models in inference mode
5. Get new segmentations
6. Aggregate segmentation results
7. Re-train models and loop...

**Provenance notes**

1. Models are trained on inferences of previous models
2. Provenance queries:
   1. "What data was used to train this model?"
3. Refer to TomoBank IDs for data identification scheme
4. Need rich metadata for search

Samarakoon/Osborn
-----------------

**Goals**

1. Fit simulated crystal structure to scattering data

**Workflow**

1. Obtain neutron scattering data
2. Apply auto-encoder to identify important features
3. Apply dimensionality reduction
4. Fit to data
