from __future__ import unicode_literals
from ctypes import c_char_p, c_void_p, cast
import os


def ccall(fname, lib, restype, argtypes, *args):
    f = getattr(lib, fname)
    f.restype = restype
    f.argtypes = argtypes
    res = f(*args)
    if restype == c_void_p or restype == c_char_p:
        return cast(res, restype)
    else:
        return res


def cglobal(vname, lib, vtype=c_void_p):
    return vtype.in_dll(lib, vname)


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def pretty_path(path):
    user_home = os.path.expanduser('~') + os.sep
    if path and path.startswith(user_home):
        path = os.path.join("~", path[len(user_home):])
    return path
