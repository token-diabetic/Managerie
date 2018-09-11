"""
Prints text in a fancy way, like in the movies.
"""

import time, sys

def printf(s, speed):
    try:
        speed = int(speed)
    except (TypeError, ValueError):
        speed = 0.005
    for c in s:
        sys.stdout.write(c)
        sys.stdout.flush()
        time.sleep(speed)
    sys.stdout.write("\n")
