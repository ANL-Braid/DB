
"""
SLAC WORKFLOW
"""

from log_tools import get_logger
import braid_db

logger = None
logger = get_logger(logger, "SLAC")

logger.info("WORKFLOW START")

db_file = "braid-slac.db"

DB = braid_db.setup_db(db_file)

logger.info("WORKFLOW STOP")
