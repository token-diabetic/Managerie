"""
Prints text in a fancy way, like in the movies.
"""

import time, sys

def printf(s, speed=10):
    if not isinstance(speed, int) or isinstance(speed, float):
        speed = 10
    for c in s:
        sys.stdout.write(c)
        sys.stdout.flush()
        time.sleep(speed / 1000)
    sys.stdout.write("\n")
