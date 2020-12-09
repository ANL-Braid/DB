
# TEST 1
# Just initialize the DB

import braid_db

braid_db.setup_db("braid.db")

db = BraidDB()
db.create("braid-db.sql")
