
# TOOLS DB CREATE
# Just initialize the DB

from braid_db import *

import argparse
parser = argparse.ArgumentParser(description="Setup the Braid DB.")
parser.add_argument("db", action="store", help="specify DB file")
args = parser.parse_args()
argvars = vars(args)

db_file = argvars["db"]

db = BraidDB(db_file)
db.create()
