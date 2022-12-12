"""
CTSegNet WORKFLOW

https://github.com/aniketkt/CTSegNet
"""

import logging

import braid_db
from braid_db import BraidData, BraidDB, BraidFact, BraidModel, BraidTagType

logger = None
# logger = get_braid_logger(logger, "CTSegNet")
logger = logging.getLogger("CTSegNet:")
logger.setLevel(logging.INFO)

logger.info("WORKFLOW START")

db_file = "braid-ctsegnet.db"
DB = BraidDB(db_file, debug=False)
DB.create()

# WORKFLOW OUTLINE
# ... Create dependency linkages along the way

# Create configuration object
number = braid_db.digits(3)
name = f"CTSegNet CFG {number}"
cfg = BraidFact(db=DB, name=name)

# Store configuration object
# Cf. https://github.com/aniketkt/CTSegNet/blob/master/cfg_files/setup_seg.cfg
cfg.store()
uri = "login.host:/home/user1/setup_seg.cfg"
cfg.add_uri(uri)

# Run experiment
# Store experiments
name = f"scan-{number}"
expt = BraidData(db=DB, name=name)
expt.store()
expt.add_derivation(cfg)
uri = f"login.host:/home/user1/{name}.data"
expt.add_uri(uri)

# Create or retrieve models
model_count = 3
models = []
# Train initial models
for model_id in range(0, model_count):
    name = f"model-{number}-{model_id:03}"
    model = BraidModel(db=DB, name=name)
    model.store()
    model.add_derivation(cfg)
    uri = "login.host:/home/user1/%s.h5" % name
    model.add_uri(uri)
    model.add_tag("model-number", str(number), type_=BraidTagType.INTEGER)
    model.add_tag("model-id", str(model_id), type_=BraidTagType.INTEGER)
    models.append(model)

iterations = 3
img = expt
for iteration in range(0, iterations):
    logger.info(f"ITERATION: {iteration}")
    # Train models
    model_id = 0
    for model in models:
        logger.info(f"TRAIN: {model_id}")
        model.add_derivation(img)
        model_id += 1
    # Apply 3D image processing
    logger.info("PROCESS:")
    name = f"image-processed-{number}-{iteration}"
    imgp = BraidData(db=DB, name=name)
    imgp.store()
    imgp.add_derivation(img)
    # Run segmenter on each model, producing masks
    model_id = 0
    for model in models:
        logger.info(f"SEGMENT: {model_id}")
        name = f"mask-{number}-{iteration}-{model_id}"
        mask = BraidData(db=DB, name=name)
        # TODO: Reload if exists
        mask.store()
        mask.add_derivation(imgp)
        model_id += 1
    # Vote
    logger.info("VOTE:")
    name = f"vote-{iteration}"
    img = BraidData(db=DB, name=name)
    img.store()
    for model in models:
        img.add_derivation(model)

logger.info("WORKFLOW STOP")


def main():
    pass


if __name__ == "__main__":
    main()
