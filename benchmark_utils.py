def benchmark(number=None, repeat=None, benchmark=None):
    def decorator(func):
        func.is_benchmark = True
        if number is not None:
            func.number = number
        if repeat is not None:
            func.repeat = repeat
        if benchmark is not None:
            func.benchmark = benchmark
        if benchmark is None:
            func.benchmark = "fast"
        return func
        
    return decorator