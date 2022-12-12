"""
SSX WORKFLOW
"""

import logging

from braid_db import BraidData, BraidDB, BraidFact, BraidModel, digits

logger = None
logger = logging.getLogger("SSX:")

logger.info("WORKFLOW START")

db_file = "braid-ssx.db"
DB = BraidDB(db_file, debug=False)
DB.create()

# WORKFLOW OUTLINE
# ... Create dependency linkages along the way
# - Log the beamline.json and phil files
# - Run the experiment*
# - Log the output files (ints)
# - Log the prime.phil file
# - Log the structure from prime/refinement

# TODO: Consider whether datablocks should be logged.

# Create configuration object
number = digits(3)
name = f"beamline_{number}"
phil_name = f"process_{number}"
cfg = BraidFact(db=DB, name=name)
phil = BraidFact(db=DB, name=phil_name)

# Store configuration objects
cfg.store()
uri = f"login.host:/home/user1/{name}.json"
cfg.add_uri(uri)

phil.store()
phil_uri = f"login.host:/home/user1/{phil_name}.phil"
phil.add_uri(phil_uri)

# Run experiment
# Store experiments
experiments = []
for x in range(10):
    name = f"int-0-{number}-{x}"
    expt = BraidData(db=DB, name=name)
    expt.store()
    expt.add_derivation(cfg)
    expt.add_derivation(phil)
    uri = f"login.host:/home/user1/{name}.pickle"
    expt.add_uri(uri)
    experiments.append(expt)

# Log the prime.phil file
name = f"prime-{number}"
prime = BraidData(db=DB, name=name)
prime.store()
prime.add_derivation(cfg)
prime.add_derivation(phil)
prime_uri = f"login.host:/home/user1/{name}.phil"
prime.add_uri(prime_uri)

# Refine structure
name = f"structure-{number}"
structure = BraidModel(db=DB, name=name)
structure.store()
for ex in experiments:
    structure.add_derivation(ex)
structure.add_derivation(prime)
structure_uri = f"login.host:/home/user1/{name}.mkv"
structure.add_uri(structure_uri)

logger.info("WORKFLOW STOP")

DB.print()


def main():
    pass  # Just a placeholder for the entry target of scripts


if __name__ == "__main__":
    main()
