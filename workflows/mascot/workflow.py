
"""
MASCOT WORKFLOW
"""

from braid_db import *
import logging
import random

logger = None
logger = logging.getLogger("Mascot:")
logger.setLevel(logging.INFO)

logger.info("WORKFLOW START")

db_file = "braid-mascot.db"
DB = BraidDB(db_file, debug=False)

# WORKFLOW OUTLINE
# ... Create dependency linkages along the way

# Number of configurations
count_configurations = 3
# Number of experiments per cycle
count_experiments    = 3
# Number of experiment cycles
count_cycles         = 1
# URIs per Record
count_uris           = 3
# Number of configuration dependencies per experiment
count_cfg_deps       = 3

# List of all configuration Facts
cfgs = []

# Create configuration objects
for i in range(0, count_configurations):
    number = digits(3)
    name = "CFG %s" % number
    cfg = BraidFact(db=DB, name=name)
    cfg.store()
    for j in range(0, count_uris):
        uri = "login.host:/home/user1/setup-%s.cfg" % digits(3)
        cfg.add_uri(uri)
    cfgs.append(cfg)

# Create or retrieve models
model_count = 3
models = []
# Train initial models
for model_id in range(0, model_count):
    name = "model-%i" % (model_id)
    model = BraidModel(db=DB, name=name)
    models.append(model)
    model.store()
    model.add_dependency(cfgs[model_id])

# Loop over experiment cycles
for i in range(0, count_cycles):
    for j in range(0, count_experiments):
        number = digits(3)
        name = "expt-%s" % number
        expt = BraidData(db=DB, name=name)
        expt.store()
        samples = random.sample(cfgs, count_cfg_deps)
        for cfg in samples:
            expt.add_dependency(cfg)
        for k in range(0, count_uris):
            uri = "login.host:/home/user1/expt-%s.data" % digits(3)
            expt.add_uri(uri)
        for model in models:
            model.add_dependency(expt)

# For Emacs/Elpy
# (elpy-rpc-pythonpath "../../src")
