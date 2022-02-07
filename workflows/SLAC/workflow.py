"""
SLAC WORKFLOW
"""

import logging

from braid_db import BraidData, BraidDB, BraidFact, BraidModel, digits

logger = None
# logger = get_braid_logger(logger, "SLAC")
logger = logging.getLogger("SLAC:")

logger.info("WORKFLOW START")

db_file = "braid-slac.db"
DB = BraidDB(db_file, debug=True)
DB.create()

# WORKFLOW OUTLINE
# ... Create dependency linkages along the way

# Create configuration object
number = digits(3)
name = f"SLAC CFG {number}"
cfg = BraidFact(db=DB, name=name)

# Store configuration object
cfg.store()
uri = "login.host:/home/user1/settings.cfg"
cfg.add_uri(uri)

# Run experiment
# Store experiments
name = "scan-%s" % number
expt = BraidData(db=DB, name=name)
expt.store()
expt.add_dependency(cfg)
uri = f"login.host:/home/user1/{name}.data"
expt.add_uri(uri)

# Run simulations
# Store simulations
name = "sim-%s" % number
sim = BraidData(db=DB, name=name)
sim.store()
sim.add_dependency(cfg)
uri1 = f"login.host:/home/user1/{name}-1.out"
uri2 = f"login.host:/home/user1/{name}-2.out"
sim.add_uri(uri1)
sim.add_uri(uri2)

# Create or retrieve model
# Train model
name = f"model-{number}"
model = BraidModel(db=DB, name=name)
model.store()
model.add_dependency(expt)
model.add_dependency(sim)
uri = f"login.host:/home/user1/{name}.h5"
model.add_uri(uri)

# Feed experiments and simulations to model training
# Ship model to FPGA
# Run model
# Store inferences

logger.info("WORKFLOW STOP")


def main():
    pass


if __name__ == "__main__":
    main()
