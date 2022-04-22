def digits(c: int) -> str:
    """Return c random digits (for random names)"""
    import random

    n = random.randint(0, 10**c)
    s = "%0*i" % (c, n)
    return s
