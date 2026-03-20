from sympy import symbols
from sympy import Matrix, Rational, sqrt
from sympy import S
from benchmark_utils import benchmark

@benchmark(benchmark="slow")
def time_eigen_vects():
    M = Matrix([
        [123, 45, 67, 89, sqrt(13)/2],
        [45, 234, 56, 78, Rational(19, 43)],
        [67, 56, 345, 90, 5*sqrt(7)/3],
        [Rational(17, 3), 12, 34, 456, sqrt(11)/7],
        [Rational(55, 17), sqrt(11)/5, 12, 34, 56]
    ])
    vecs = M.eigenvects()
    for val, mult, vec_list in vecs:
        assert len(vec_list) == 1
        diff = (M*vec_list[0]).n() - (val*vec_list[0]).n()
        assert all(abs(x) < 1e-10 for x in diff)
    return vecs

@benchmark()
def time_eigen_vals():
    x, y, z = symbols('x y z')
    A = Matrix(8, 8, ([1+x, 1-x]*4 + [1-x, 1+x]*4)*4)
    result = A.eigenvals()
    assert result == {8: 1, 8*x: 1, 0: 6}
    return result

@benchmark()
def time_determinant():
    mat =  Matrix(S('''[
            [             -3/4,       45/32 - 37*I/16,         1/4 + I/2,      -129/64 - 9*I/64,      1/4 - 5*I/16,      65/128 + 87*I/64,         -9/32 - I/16,      183/256 - 97*I/128],
            [-149/64 + 49*I/32, -177/128 - 1369*I/128,  125/64 + 87*I/64, -2063/256 + 541*I/128,  85/256 - 33*I/16,  805/128 + 2415*I/512, -219/128 + 115*I/256, 6301/4096 - 6609*I/1024],
            [          1/2 - I,         9/4 + 55*I/16,              -3/4,       45/32 - 37*I/16,         1/4 + I/2,      -129/64 - 9*I/64,         1/4 - 5*I/16,        65/128 + 87*I/64],
            [   -5/8 - 39*I/16,   2473/256 + 137*I/64, -149/64 + 49*I/32, -177/128 - 1369*I/128,  125/64 + 87*I/64, -2063/256 + 541*I/128,     85/256 - 33*I/16,    805/128 + 2415*I/512],
            [            1 + I,         -19/4 + 5*I/4,           1/2 - I,         9/4 + 55*I/16,              -3/4,       45/32 - 37*I/16,            1/4 + I/2,        -129/64 - 9*I/64],
            [         21/8 + I,    -537/64 + 143*I/16,    -5/8 - 39*I/16,   2473/256 + 137*I/64, -149/64 + 49*I/32, -177/128 - 1369*I/128,     125/64 + 87*I/64,   -2063/256 + 541*I/128],
            [               -2,         17/4 - 13*I/2,             1 + I,         -19/4 + 5*I/4,           1/2 - I,         9/4 + 55*I/16,                 -3/4,         45/32 - 37*I/16],
            [     1/4 + 13*I/4,    -825/64 - 147*I/32,          21/8 + I,    -537/64 + 143*I/16,    -5/8 - 39*I/16,   2473/256 + 137*I/64,    -149/64 + 49*I/32,   -177/128 - 1369*I/128]]'''))
    result = mat.det()
    assert result == 0
    return result