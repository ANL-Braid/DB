
"""
SLAC WORKFLOW
"""

import os

from log_tools import get_logger
import braid_db
from braid_db import BraidDB, BraidFact


logger = None
logger = get_logger(logger, "SLAC")

logger.info("WORKFLOW START")

db_file = "braid-slac.db"

braid_db.setup_db(db_file)
BSQL = BraidDB()

if not os.path.exists(db_file):
    BSQL.create()

# WORKFLOW OUTLINE
# ... Create dependency linkages along the way
# Create configuration object
cfg = BraidFact(uri="login.host:/home/user1/settings.cfg", name="SLAC CFG 1")
# Store configuration object
cfg.store(BSQL)
# Run experiment
# Store experiments
# Run simulations
# Store simulations
# Create or retrieve model
# Feed experiments and simulations to model training
# Ship model to FPGA
# Run model
# Store inferences

logger.info("WORKFLOW STOP")
