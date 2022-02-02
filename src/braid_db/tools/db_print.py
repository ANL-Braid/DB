# TOOLS DB PRINT
# Just print the DB

import argparse

from braid_db import BraidDB


def main():
    parser = argparse.ArgumentParser(description="Print the Braid DB.")
    parser.add_argument("db", action="store", help="specify DB file")
    args = parser.parse_args()
    argvars = vars(args)

    db_file = argvars["db"]

    db = BraidDB(db_file)
    db.print()


if __name__ == "__main__":
    main()
