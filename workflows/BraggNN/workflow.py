"""
SLAC WORKFLOW
"""

import logging

from braid_db import BraidDB

logger = logging.getLogger("BraggNN")

logger.info("WORKFLOW START")

db_file = "braid-braggnn.db"

DB = BraidDB(db_file)
DB.create()

logger.info("WORKFLOW STOP")


def main():
    pass


if __name__ == "__main__":
    main()
