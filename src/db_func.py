
# DB FUNC
# Braid DataBase Functional interface

from pprint import pprint

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
    print("insert_fact!")
    # from db_func import db_setup
    # db = db_setup()
    # cfg = BraidFact(db, name)
    # cfg.store()
    # for uri in uris:
    #     cfg.add_uri(uri)


def F():
    import os, platform
    return "Hello World: " + str(os.getcwd()) + " " + str(platform.uname())


def get_function(L, token):
    """
    Find the most recent matching function
    L: List of function dicts
    token: A token to match in the function description
    @return: The string function UUID, or None if nothing was found
    """
    import re
    hits = []  # List of functions that match the token
    for index, entry in enumerate(L):
        description = entry["description"]
        uuid = entry["function_uuid"]
        if token not in description:
            continue
        m = re.match(".*date=(.*)\\b", description)
        if m is None:
            continue
        timestamp = m[1]
        print(timestamp + " " + uuid)
        hits.append([timestamp, index])
    print("found %i matching functions" % len(hits))
    if len(hits) == 0:
        return None
    hits.sort()  # Sort the list by timestamp
    latest = hits[-1][1]
    print("latest: %i" % latest)
    function_dict = L[latest]
    return function_dict["function_uuid"]


def register_functions(fxc):
    from datetime import datetime
    timestamp = datetime.now()
    timestamp_string = timestamp.strftime("date=%Y-%m-%d_%H:%M:%S")
    description = "Braid-DB.insert_fact " + timestamp_string
    F_id = fxc.register_function(insert_fact,
                                 description=description)
    print("registered: insert_fact: " + F_id)


def main():
    fxc = FuncXClient()

    # register_functions(fxc)

    results = fxc.search_function("Braid-DB.insert_fact")
    # print(str(results))
    # for result in results:
    # print(str(result))
    # print(str(type(result)))
    # pprint(result)
    # json.dumps(result, indent=2)
    F_id = get_function(results, "Braid-DB.insert")
    if F_id is None:
        print("No functions found!")
        exit()
    print("F_id " + F_id)


if __name__ == "__main__":
    main()
