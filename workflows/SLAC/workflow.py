
"""
SLAC WORKFLOW
"""

import os

import braid_db
from braid_db import *
import logging


logger = None
# logger = get_braid_logger(logger, "SLAC")
logger = logging.getLogger("SLAC:")

logger.info("WORKFLOW START")

db_file = "braid-slac.db"
DB = BraidDB(db_file, debug=True)

# WORKFLOW OUTLINE
# ... Create dependency linkages along the way

# Create configuration object
number = braid_db.digits(3)
name = "SLAC CFG %s" % number
cfg = BraidFact(db=DB, name=name)

# Store configuration object
cfg.store()
uri = "login.host:/home/user1/settings.cfg"
cfg.add_uri(uri)

# Run experiment
# Store experiments
name = "scan-%s" % number
expt = BraidData(db=DB, name=name)
expt.store()
expt.add_dependency(cfg)
uri = "login.host:/home/user1/%s.data" % name
expt.add_uri(uri)

# Run simulations
# Store simulations
name = "sim-%s" % number
sim = BraidData(db=DB, name=name)
sim.store()
sim.add_dependency(cfg)
uri1 = "login.host:/home/user1/%s-1.out" % name
uri2 = "login.host:/home/user1/%s-2.out" % name
sim.add_uri(uri1)
sim.add_uri(uri2)

# Create or retrieve model
# Train model
name = "model-%s" % number
model = BraidModel(db=DB, name=name)
model.store()
model.add_dependency(expt)
model.add_dependency(sim)
uri = "login.host:/home/user1/%s.h5" % name
model.add_uri(uri)

# Feed experiments and simulations to model training
# Ship model to FPGA
# Run model
# Store inferences



logger.info("WORKFLOW STOP")
