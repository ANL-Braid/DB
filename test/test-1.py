
# TEST 1
# Just initialize the DB

from braid_db import *

setup_db("braid.db")

db = BraidDB()
db.create()
