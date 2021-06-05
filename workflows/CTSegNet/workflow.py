
"""
CTSegNet WORKFLOW

https://github.com/aniketkt/CTSegNet
"""

import braid_db
from braid_db import *
import logging


logger = None
# logger = get_braid_logger(logger, "CTSegNet")
logger = logging.getLogger("CTSegNet:")
logger.setLevel(logging.INFO)

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

# Create or retrieve models
model_count = 3
models = []
# Train initial models
for model_id in range(0, model_count):
    name = "model-%s-%i" % (number, model_id)
    model = BraidModel(db=DB, name=name)
    model.store()
    model.add_dependency(cfg)
    uri = "login.host:/home/user1/%s.h5" % name
    model.add_uri(uri)
    model.add_tag("model-number", str(number),
                  type_=BraidTagType.INTEGER)
    model.add_tag("model-id", str(model_id),
                  type_=BraidTagType.INTEGER)
    models.append(model)

iterations = 3
img = expt
for iteration in range(0, iterations):
    logger.info("ITERATION: %i" % iteration)
    # Train models
    model_id = 0
    for model in models:
        logger.info("TRAIN: %i" % model_id)
        model.add_dependency(img)
        model_id += 1
    # Apply 3D image processing
    logger.info("PROCESS:")
    name = "image-processed-%s-%i" % (number, iteration)
    imgp = BraidData(db=DB, name=name)
    imgp.store()
    imgp.add_dependency(img)
    # Run segmenter on each model, producing masks
    model_id = 0
    for model in models:
        logger.info("SEGMENT: %i" % model_id)
        name = "mask-%s-%i-%i" % (number, iteration, model_id)
        mask = BraidData(db=DB, name=name)
        # TODO: Reload if exists
        mask.store()
        mask.add_dependency(imgp)
        model_id += 1
    # Vote
    logger.info("VOTE:")
    name = "vote-%i" % iteration
    img = BraidData(db=DB, name=name)
    img.store()
    for model in models:
        img.add_dependency(model)

logger.info("WORKFLOW STOP")
