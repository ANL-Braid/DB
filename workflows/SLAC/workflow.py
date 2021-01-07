
"""
SLAC WORKFLOW
"""

import os

from log_tools import get_logger
import braid_db

logger = None
logger = get_logger(logger, "SLAC")

logger.info("WORKFLOW START")

db_file = "braid-slac.db"

braid_db.setup_db(db_file)
BSQL = braid_db.BraidDB()

if not os.path.exists(db_file):
    BSQL.create()

# WORKFLOW OUTLINE
# ... Create dependency linkages along the way
# Create configuration object
# Store configuration object
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
