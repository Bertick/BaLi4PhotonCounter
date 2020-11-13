from functools import wraps
import logging
import numpy as np


def debug(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        logging.debug(f"Function {f.__name__} was called")
        return f(*args, **kwargs)
    return wrapper


@debug
def C8855Open():
    return 1


@debug
def C8855Close(handle):
    return 1


@debug
def C8855Reset(hhandle):
    return 1


@debug
def C8855CountStart(hhandle, trig):
    return 1


@debug
def C8855CountStop(hhandle):
    return 1


@debug
def C8855Setup(hhandle, times, mode_c, n_gates_c):
    return 1


@debug
def C8855SetPmtPower(hhandle, pow_mode):
    return 1


@debug
def C8855ReadData(hhandle, data, result):
    from ctypes import c_uint32, cast, POINTER

    pnt = cast(data, POINTER(c_uint32))

    for i in range(5):
        pnt[i] = c_uint32(np.random.randint(30, 50))
    return 1


@debug
def C8855ReadId(hhandle, uid):
    return 1