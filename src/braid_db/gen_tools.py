import random
from typing import Any, Dict


def digits(c: int) -> str:
    """Return c random digits (for random names)"""

    n = random.randint(0, 10**c)
    s = "%0*i" % (c, n)
    return s


def substitute_vals(val: Any, substitution_vals: Dict[str, str]) -> Any:
    if isinstance(val, str):
        val = val.format(**substitution_vals)
    elif isinstance(val, dict):
        val = {
            k: substitute_vals(v, substitution_vals) for k, v in val.items()
        }
    elif isinstance(val, list):
        val = [substitute_vals(i, substitution_vals) for i in val]
    return val
