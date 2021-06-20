
"""
MASCOT WORKFLOW
"""

import logging
import random
import time

from braid_db import *


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description=
                                     "Run a synthetic workflow")
    parser.add_argument("--db", type=str,
                        default='braid-mascot.db',
                        help="DB file name")
    parser.add_argument("--configurations", type=int, default=5,
                        help="Number of configurations")
    parser.add_argument("--experiments", type=int, default=3,
                        help="Number of experiments")
    parser.add_argument("--cycles", type=int, default=5,
                        help="Number of experiment cycles")
    parser.add_argument("--uris", type=int, default=3,
                        help="Number of URIs per record")
    parser.add_argument("--deps", type=int, default=3,
                        help="""Number of configuration dependencies
                                per experiment""")
    parser.add_argument("--models", type=int, default=3,
                        help="Number of models")
    parser.add_argument("--time", default=False, action="store_true",
                        help="Report run time")
    parser.add_argument("--verbose", type=int, default=0,
                        help="Logger verbosity: 0=least, 1, 2=most")

    args = parser.parse_args()
    return args


args = parse_args()

logger = None
logger = logging.getLogger("Mascot:")

level = logging.WARN
if args.verbose == 1:
    level = logging.INFO
elif args.verbose == 2:
    level = logging.DEBUG
logger.setLevel(level)

logger.info("WORKFLOW START")

db_file = args.db
DB = BraidDB(db_file,
             log=(args.verbose>0),
             debug=(args.verbose>1))

# WORKFLOW OUTLINE
# ... Create dependency linkages along the way

# Number of configurations
count_configurations = args.configurations
# Number of experiments per cycle
count_experiments    = args.experiments
# Number of experiment cycles
count_cycles         = args.cycles
# URIs per Record
count_uris           = args.uris
# Number of configuration dependencies per experiment
count_cfg_deps       = args.deps
count_models         = args.models

if count_models > count_configurations:
    logger.fatal("mascot: FATAL: " +
                 "configurations=%i must be >= models=%i" %
                 (count_configurations, count_models))
    exit(1)

# List of all configuration Facts
cfgs = []

time_start = time.time()

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
models = []
# Train initial models
for model_id in range(0, count_models):
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

time_stop = time.time()
if args.time:
    duration = time_stop - time_start
    print("mascot time: %0.4f" % duration)
    size = DB.size()
    print("mascot size: %i" % size)
    print("mascot rate: %0.4f" % (size/duration))

# For Emacs/Elpy
# (elpy-rpc-pythonpath "../../src")
