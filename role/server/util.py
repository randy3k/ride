from ctypes import c_char_p, c_char, c_int, c_void_p, cast, POINTER


def ccall(fname, lib, restype, argtypes, *args):
    f = getattr(lib, fname)
    f.restype = restype
    f.argtypes = argtypes
    res = f(*args)
    if restype == c_void_p or restype == c_char_p:
        return cast(res, restype)
    else:
        return res


def cglobal(vname, lib, vtype):
    return vtype.in_dll(lib, vname)


def is_ascii(s):
    return all(ord(c) < 128 for c in s)
