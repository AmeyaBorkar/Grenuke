"""python peak.py script.py [args...]: run a script and print its peak working set."""
import runpy
import sys
import time

import psutil

t = time.time()
sys.argv = sys.argv[1:]
try:
    runpy.run_path(sys.argv[0], run_name="__main__")
finally:
    print("peak GB", round(psutil.Process().memory_info().peak_wset / 1e9, 2), round(time.time() - t), "s", flush=True)
