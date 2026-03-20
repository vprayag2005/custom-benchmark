from setuptools import setup, find_packages

setup(
    name="sympy-benchmark",
    version="0.1.0",
    py_modules=["runner", "benchmark_utils"],
    install_requires=[
        "tabulate",
    ],
    entry_points={
        "console_scripts": [
            "sympy-benchmark=runner:main",
        ],
    },
)
