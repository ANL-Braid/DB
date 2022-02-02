# TOOLS DB CREATE
# Just initialize the DB

import argparse
import os

from braid_db import BraidDB


def find_next_bak(filename):
    i = 1
    while True:
        fn = f"{filename}.{i:03}.bak"
        if not os.path.exists(fn):
            return fn
        i += 1
    # unreachable
    assert False


def main():
    parser = argparse.ArgumentParser(description="Setup the Braid DB.")
    parser.add_argument(
        "-B", action="store_true", help="Move an existing DB to a backup"
    )
    parser.add_argument("-v", action="store_true", help="Be verbose")
    parser.add_argument("db", action="store", help="specify DB file")
    args = parser.parse_args()
    argvars = vars(args)

    db_file = argvars["db"]

    if argvars["B"]:
        if os.path.exists(db_file):
            db_file_bak = find_next_bak(db_file)
            print(f"db-create.py: renaming {db_file} -> {db_file_bak}")
            os.rename(db_file, db_file_bak)

    if argvars["v"]:
        print(f"db-create.py: creating: {os.path.realpath(db_file)}")

    db = BraidDB(db_file)
    db.create()


if __name__ == "__main__":
    main()
