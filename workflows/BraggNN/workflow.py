
"""
SLAC WORKFLOW
"""

from braid_db import *

logger = logging.getLogger("BraggNN")

logger.info("WORKFLOW START")

db_file = "braid-braggnn.db"

DB = BraidDB(db_file)

logger.info("WORKFLOW STOP")
