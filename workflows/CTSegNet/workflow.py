
"""
CTSegNet WORKFLOW
"""

import os

import braid_db
from braid_db import *
import logging


logger = None
# logger = get_braid_logger(logger, "CTSegNet")
logger = logging.getLogger("CTSegNet:")

logger.info("WORKFLOW START")

db_file = "braid-ctsegnet.db"
DB = BraidDB(db_file, debug=False)

# WORKFLOW OUTLINE
# ... Create dependency linkages along the way

# Create configuration object
number = braid_db.digits(3)
name = "CTSegNet CFG %s" % number
cfg = BraidFact(db=DB, name=name)

# Store configuration object
# Cf. https://github.com/aniketkt/CTSegNet/blob/master/cfg_files/setup_seg.cfg
cfg.store()
uri = "login.host:/home/user1/setup_seg.cfg"
cfg.add_uri(uri)

# Run experiment
# Store experiments
name = "scan-%s" % number
expt = BraidData(db=DB, name=name)
expt.store()
expt.add_dependency(cfg)
uri = "login.host:/home/user1/%s.data" % name
expt.add_uri(uri)

# Create or retrieve model
# Train initial model
name = "model-%s" % number
model = BraidModel(db=DB, name=name)
model.store()
model.add_dependency(cfg)
model.add_dependency(expt)
uri = "login.host:/home/user1/%s.h5" % name
model.add_uri(uri)
model.add_tag("model-number", str(number),
              type_=BraidTagType.INTEGER)


logger.info("WORKFLOW STOP")
