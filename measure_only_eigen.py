import sys
import time
import pathlib

# Setup paths to match the environment
ROOT = pathlib.Path(r"c:\OpenSource\sympy").resolve()
SUB_PROJ = ROOT / "custom_benchmark"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import sympy
from sympy import Matrix, Rational, sqrt

M = Matrix([
    [123, 45, 67, 89, sqrt(13)/2],
    [45, 234, 56, 78, Rational(19, 43)],
    [67, 56, 345, 90, 5*sqrt(7)/3],
    [Rational(17, 3), 12, 34, 456, sqrt(11)/7],
    [Rational(55, 17), sqrt(11)/5, 12, 34, 56]
])

print(f"--- Run 1 (Cold inside process) ---")
t0 = time.perf_counter()
res1 = M.eigenvects()
t1 = time.perf_counter()
print(f"Time: {t1 - t0:.4f}s")

print(f"\n--- Run 2 (Warm inside process) ---")
t2 = time.perf_counter()
res2 = M.eigenvects()
t3 = time.perf_counter()
print(f"Time: {t3 - t2:.4f}s")
