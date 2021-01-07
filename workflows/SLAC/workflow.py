
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

logger.info("WORKFLOW STOP")
