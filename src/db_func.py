
# DB FUNC
# Braid DataBase Functional interface

from funcx.sdk.client import FuncXClient

from braid_db import BraidDB, BraidFact


def funcx_register():
    # braid_fu
    pass


def db_setup():
    db_file = "func.db"
    db = BraidDB(db_file, log=True)
    return db


def insert_fact(name, uris):
    """
    uris: list of string: the URIs for this Fact
    """
    db = db_setup()
    cfg = BraidFact(db, name)
    cfg.store()
    for uri in uris:
        cfg.add_uri(uri)


def F():
    import os, platform
    return "Hello World: " + str(os.getcwd()) + " " + str(platform.uname())


def main():
    fxc = FuncXClient()
    # F_id = fxc.register_function(F, description="Braid F")
    # print("F_id: %r" % F_id)
    results = fxc.search_function("Braid")
    print(str(results))


if __name__ == "__main__":
    main()
