import dataclasses
import importlib.util
import inspect
import json
import pathlib
import subprocess
import sys
import time
import gc
import argparse
import textwrap
import tempfile
import shutil
from tabulate import tabulate

PROJ_ROOT = pathlib.Path(__file__).resolve().parent
SNAP_FILE = PROJ_ROOT / "results.snap.json"


@dataclasses.dataclass
class BenchmarkResult:
    key: str
    status: str
    elapsed: float
    output: str


class ResultFormatter:
    def table(self, rows, headers):
        print("\n" + tabulate(rows, headers=headers, tablefmt="grid"))


class BenchmarkRunner:
    def __init__(self, mode="cold"):
        self.mode = mode
        self.baselines = json.loads(SNAP_FILE.read_text()) if SNAP_FILE.exists() else {}
        self.formatter = ResultFormatter()
        self.active_root = None

    def _clone_upstream(self):
        print("Cloning latest SymPy from GitHub...")
        temp_dir = tempfile.mkdtemp()
        try:
            subprocess.run(["git", "clone", "--depth", "1", "https://github.com/sympy/sympy.git", temp_dir], check=True, capture_output=True)
            self.active_root = pathlib.Path(temp_dir)
            return temp_dir
        except Exception as e:
            if pathlib.Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
            raise RuntimeError(f"Failed to clone SymPy: {e}")

    def _save_snap(self, active_keys):
        pruned = {k: v for k, v in self.baselines.items() if k in active_keys}
        SNAP_FILE.write_text(json.dumps(pruned, indent=4))

    def discover(self, directory=None):
        if directory is None:
            directory = PROJ_ROOT / "benchmarks" / "sympy-benchmark"
        base_path = pathlib.Path(directory)
        if not base_path.exists():
            return []

        paths = [str(PROJ_ROOT), str(base_path.resolve())]
        if self.active_root:
            paths.insert(0, str(self.active_root))
            
        for p in paths:
            if p not in sys.path:
                sys.path.insert(0, p)

        benchmarks = []
        for filepath in base_path.rglob("*.py"):
            if filepath.name == "__init__.py":
                continue
            lib_key = f"{base_path.name.replace('-', '_')}__{filepath.stem}"
            spec = importlib.util.spec_from_file_location(lib_key, str(filepath))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[lib_key] = module
                spec.loader.exec_module(module)
                for _, obj in inspect.getmembers(module):
                    if inspect.isfunction(obj) and getattr(obj, "is_benchmark", False):
                        obj._module_name = filepath.stem
                        obj._filepath = str(filepath)
                        benchmarks.append(obj)
        return benchmarks

    def _calibrate_warm(self, func):
        number = 1
        while True:
            gcold = gc.isenabled()
            gc.disable()
            try:
                t = time.perf_counter()
                for _ in range(number):
                    func()
                elapsed = time.perf_counter() - t
            finally:
                if gcold:
                    gc.enable()
            if elapsed >= 0.1 or number >= 100000:
                break
            number *= 10
        return number

    def _calibrate_cold(self, func):
        root_path = str(self.active_root).replace('\\', '/') if self.active_root else ""
        proj_path = str(PROJ_ROOT).replace('\\', '/')
        root_setup = f"'{root_path}', " if root_path else ""
        fp = func._filepath.replace('\\', '/')
        code = textwrap.dedent(f'''
            import sys, time, importlib.util, gc
            sys.path[0:0] = [{root_setup}'{proj_path}']
            spec = importlib.util.spec_from_file_location("{func._module_name}", "{fp}")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            f = getattr(mod, "{func.__name__}")
            from sympy.core.cache import clear_cache
            n = 1
            while True:
                gcold = gc.isenabled()
                gc.disable()
                try:
                    t = time.perf_counter()
                    for _ in range(n):
                        clear_cache()
                        f()
                    elapsed = time.perf_counter() - t
                finally:
                    if gcold:
                        gc.enable()
                if elapsed >= 0.1 or n >= 10000: break
                n *= 10
            print(n)
        ''')
        res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        return int(res.stdout.strip().split("\n")[-1]) if res.returncode == 0 and res.stdout else 1

    def _execute(self, func, number, repeat):
        times = []
        fp = func._filepath.replace('\\', '/')
        for _ in range(repeat):
            if self.mode == "warm":
                gcold = gc.isenabled()
                gc.disable()
                try:
                    t = time.perf_counter()
                    for _ in range(number):
                        func()
                    times.append((time.perf_counter() - t) / number)
                finally:
                    if gcold:
                        gc.enable()
            else:
                root_path = str(self.active_root).replace('\\', '/') if self.active_root else ""
                proj_path = str(PROJ_ROOT).replace('\\', '/')
                root_setup = f"'{root_path}', " if root_path else ""
                code = textwrap.dedent(f'''
                    import sys, time, importlib.util, gc
                    sys.path[0:0] = [{root_setup}'{proj_path}']
                    spec = importlib.util.spec_from_file_location("{func._module_name}", "{fp}")
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    f = getattr(mod, "{func.__name__}")
                    from sympy.core.cache import clear_cache
                    gcold = gc.isenabled()
                    gc.disable()
                    try:
                        t = time.perf_counter()
                        for _ in range({number}):
                            clear_cache()
                            f()
                        print(time.perf_counter() - t)
                    finally:
                        if gcold:
                            gc.enable()
                ''')
                res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
                if res.returncode == 0 and res.stdout:
                    times.append(float(res.stdout.strip().split("\n")[-1]) / number)
        return times

    def run(self, func, update=False):
        key = f"{func._module_name}.py::{func.__name__}"
        try:
            out = str(func())
        except Exception as e:
            return BenchmarkResult(key, f"FAIL ({type(e).__name__})", 0.0, "")

        num = getattr(func, "number", None)
        rep = getattr(func, "repeat", 5)
        if num is None:
            num = self._calibrate_warm(func) if self.mode == "warm" else self._calibrate_cold(func)

        times = self._execute(func, num, rep)
        elapsed = min(times) if times else 0.0

        if update:
            self.baselines.setdefault(key, {})["time_s"] = round(elapsed, 4)

        return BenchmarkResult(key, "PASS", elapsed, out)

    def run_all(self, bench_filter="", update=False):
        temp_dir = None
        try:
            temp_dir = self._clone_upstream()
            benchmarks = self.discover()
            if bench_filter:
                active = set(t.strip() for t in bench_filter.split(",") if t.strip())
                benchmarks = [f for f in benchmarks if getattr(f, "benchmark", "fast") in active]

            rows = []
            for f in benchmarks:
                r = self.run(f, update=update)
                rows.append([r.key, r.status, f"{r.elapsed:.4f}s"])

            self.formatter.table(rows, headers=["Benchmark Name", "Correctness", "Time"])

            if update:
                self._save_snap({f"{f._module_name}.py::{f.__name__}" for f in benchmarks})
                print("\nSnapshot updated.")
        finally:
            if temp_dir and pathlib.Path(temp_dir).exists():
                def on_rm_error(func, path, exc_info):
                    import os, stat
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                shutil.rmtree(temp_dir, onerror=on_rm_error)
                self.active_root = None

    def compare(self, libraries, benchmark_filter=""):
        bench_dir = PROJ_ROOT / "benchmarks"
        for lib in libraries:
            if not (bench_dir / lib).exists():
                print(f"Error: {lib} not found")
                return

        lib_bench = {lib: {f.__name__: f for f in self.discover(bench_dir / lib)} for lib in libraries}

        if benchmark_filter:
            req = set(t.strip() for t in benchmark_filter.split(",") if t.strip())
            for lib in libraries:
                lib_bench[lib] = {n: f for n, f in lib_bench[lib].items() if n in req}

        all_names = sorted(set().union(*(lb.keys() for lb in lib_bench.values())))
        if not all_names:
            print("No benchmarks found.")
            return

        rows = []
        for name in all_names:
            row = [name]
            for lib in libraries:
                f = lib_bench[lib].get(name)
                if not f:
                    row.append("N/A")
                    continue
                r = self.run(f)
                if r.status == "PASS":
                    out_disp = (r.output[:60] + "...") if len(r.output) > 60 else r.output
                    row.append(f"{r.elapsed:.4f}s\no/p: {out_disp}")
                else:
                    row.append(r.status)
            rows.append(row)

        self.formatter.table(rows, headers=["Benchmark Name"] + libraries)


def main():
    parser = argparse.ArgumentParser(description="SymPy Snapshot Benchmark Runner")
    subparsers = parser.add_subparsers(dest="command")

    run_p = subparsers.add_parser("run")
    run_p.add_argument("--cache-mode", "--cache", choices=["cold", "warm"], default="cold")
    run_p.add_argument("--bench", default="")
    run_p.add_argument("--update", action="store_true")

    cmp_p = subparsers.add_parser("compare")
    cmp_p.add_argument("libraries", nargs="+")
    cmp_p.add_argument("--benchmark", default="")
    cmp_p.add_argument("--cache-mode", "--cache", choices=["cold", "warm"], default="cold")

    args = parser.parse_args()

    if args.command == "run":
        BenchmarkRunner(mode=args.cache_mode).run_all(bench_filter=args.bench, update=args.update)
    elif args.command == "compare":
        BenchmarkRunner(mode=args.cache_mode).compare(args.libraries, benchmark_filter=args.benchmark)
    else:
        parser.print_help()


if __name__ == "__main__":
    sys.exit(main())
