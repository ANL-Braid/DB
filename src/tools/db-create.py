
# TOOLS DB CREATE
# Just initialize the DB

from braid_db import *

import argparse
parser = argparse.ArgumentParser(description="Setup the Braid DB.")
parser.add_argument("-B", action="store_true",
                    help="Move an existing DB to a backup")
parser.add_argument("db", action="store", help="specify DB file")
args = parser.parse_args()
argvars = vars(args)

db_file = argvars["db"]


def find_next_bak(filename):
    i = 1
    while True:
        fn = "%s.%03i.bak" % (filename, i)
        if not os.path.exists(fn):
            return fn
        i += 1
    # unreachable
    assert False


if argvars["B"] is not None:
    import os
    if os.path.exists(db_file):
        db_file_bak = find_next_bak(db_file)
        print("db-create.py: renaming %s -> %s" % (db_file, db_file_bak))
        os.rename(db_file, db_file_bak)

db = BraidDB(db_file)
db.create()
