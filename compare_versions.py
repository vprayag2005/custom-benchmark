import sys
import time
import pathlib

def run_test(use_local):
    # Prepare script content
    local_path = r"c:\OpenSource\sympy"
    setup_path = f"sys.path.insert(0, r'{local_path}')" if use_local else "pass"
    
    code = f'''
import sys
{setup_path}
import sympy
import time
from sympy import Matrix, Rational, sqrt

M = Matrix([
    [123, 45, 67, 89, sqrt(13)/2],
    [45, 234, 56, 78, Rational(19, 43)],
    [67, 56, 345, 90, 5*sqrt(7)/3],
    [Rational(17, 3), 12, 34, 456, sqrt(11)/7],
    [Rational(55, 17), sqrt(11)/5, 12, 34, 56]
])

t0 = time.perf_counter()
M.eigenvects()
print(f"{{time.perf_counter() - t0:.4f}}", end="")
'''
    import subprocess
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error for {'local' if use_local else 'system'}: {res.stderr}")
    return float(res.stdout.strip()) if res.stdout else None

print("Comparing SymPy Versions Performance...")

local_time = run_test(True)
print(f"SymPy 1.15.0.dev (Local): {local_time}s")

system_time = run_test(False)
print(f"SymPy 1.14.0 (System): {system_time}s")

if local_time and system_time:
    diff = system_time - local_time
    pct = (diff / system_time) * 100
    print(f"\nDifference: {diff:.4f}s ({pct:.1f}% faster)" if diff > 0 else f"\nDifference: {-diff:.4f}s ({-pct:.1f}% slower)")
