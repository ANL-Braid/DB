
# TOOLS DB PRINT
# Just print the DB

from braid_db import *

import argparse
parser = argparse.ArgumentParser(description="Print the Braid DB.")
parser.add_argument("db", action="store", help="specify DB file")
args = parser.parse_args()
argvars = vars(args)

db_file = argvars["db"]

setup_db(db_file)

db = BraidDB()
db.print()
