# SymPy Custom Benchmark Tool

## Setup
Install dependencies using `pip`:
```bash
pip install -r requirements.txt
```

To install the tool as a CLI command:
```bash
pip install -e .
```

## Usage
Run all benchmarks:
```bash
sympy-benchmark run
```

Compare specific libraries:
```bash
sympy-benchmark compare sympy-benchmark flint-benchmark
```

Update baselines:
```bash
sympy-benchmark run --update
```

## Disclaimer
> [!IMPORTANT]
> Since this is a prototype, the code is mostly written by an LLM.
