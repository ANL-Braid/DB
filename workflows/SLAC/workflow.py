
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
DB = BraidDB(db_file, debug=False)

# WORKFLOW OUTLINE
# ... Create dependency linkages along the way

# Create configuration object
number = braid_db.digits(3)
name = "SLAC CFG %s" % number
cfg = BraidFact(db=DB,
                uri="login.host:/home/user1/settings.cfg",
                name=name)

# Store configuration object
cfg.store()

# Run experiment
# Store experiments
name = "scan-%s" % number
expt = BraidData(db=DB,
                 uri="login.host:/home/user1/%s.cfg" % name,
                 name=name)
expt.store()
expt.add_dependency(cfg)

# Run simulations
# Store simulations
name = "sim-%s" % number
sim = BraidData(db=DB,
                uri="login.host:/home/user1/%s.cfg" % name,
                name=name)
sim.store()
sim.add_dependency(cfg)

# Create or retrieve model
# Train model
name = "model-%s" % name
model = BraidModel(db=DB,
                   uri="login.host:/home/user1/%s.cfg" % name,
                   name=name)
model.store()
model.add_dependency(expt)
model.add_dependency(sim)

# Feed experiments and simulations to model training
# Ship model to FPGA
# Run model
# Store inferences



logger.info("WORKFLOW STOP")
