from ctypes import c_char_p, c_char, c_int, c_double, c_void_p, cast, addressof, POINTER
import sys

from .util import ccall, cglobal

# to be set later
rinstance = None

"""
A minimum set of R api functions to make the repl works.
"""


NILSXP = 0
SYMSXP = 1
LISTSXP = 2
CLOSXP = 3
ENVSXP = 4
PROMSXP = 5
LANGSXP = 6
SPECIALSXP = 7
BUILTINSXP = 8
CHARSXP = 9
LGLSXP = 10
INTSXP = 13
REALSXP = 14
CPLXSXP = 15
STRSXP = 16
DOTSXP = 17
ANYSXP = 18
VECSXP = 19
EXPRSXP = 20
BCODESXP = 21
EXTPTRSXP = 22
WEAKREFSXP = 23
RAWSXP = 24
S4SXP = 25
NEWSXP = 30
FREESXP = 31
FUNSXP = 99


rglobal_dict = {}


def rccall(fname, *args):
    return ccall(fname, rinstance.libR, *args)


def rcglobal(vname, cast_type=c_void_p):
    if cast_type == c_void_p:
        if vname not in rglobal_dict:
            rglobal_dict[vname] = cglobal(vname, rinstance.libR, c_void_p)
        return rglobal_dict[vname]
    else:
        return cglobal(vname, rinstance.libR, cast_type)


def process_events():
    if sys.platform == "win32" or sys.platform == "darwin":
        rccall("R_ProcessEvents", None, None)
    if sys.platform.startswith("linux") or sys.platform == "darwin":
        what = rccall("R_checkActivity", c_void_p, [c_int, c_int], 0, 1)
        if what.value:
            R_InputHandlers = rcglobal("R_InputHandlers")
            rccall("R_runHandlers", None, [c_void_p, c_void_p], R_InputHandlers, what)


def preserve_object(s):
    return rccall("R_PreserveObject", c_void_p, [c_void_p], s)


def release_object(i):
    return rccall("R_ReleaseObject", c_void_p, [c_int], i)


def protect(s):
    return rccall("Rf_protect", c_void_p, [c_void_p], s)


def unprotect(i):
    return rccall("Rf_unprotect", c_void_p, [c_int], i)


def mk_symbol(s):
    return rccall("Rf_install", c_void_p, [c_char_p], s.encode("utf-8"))


def mk_string(s):
    return rccall("Rf_mkString", c_void_p, [c_char_p], s.encode("utf-8"))


def scalar_integer(i):
    return rccall("Rf_ScalarInteger", c_void_p, [c_int], i)


def parse_vector(s):
    status = c_int()
    val = rccall(
        "R_ParseVector",
        c_void_p,
        [c_void_p, c_int, POINTER(c_int), c_void_p],
        s, -1, status, rcglobal("R_NilValue"))
    return val, status.value


def parse_error_msg():
    return cast(addressof(rcglobal("R_ParseErrorMsg", c_char)), c_char_p).value.decode("utf-8")


def length(s):
    return rccall("Rf_length", c_int, [c_void_p], s)


def dataptr_type(s):
    typ = typeof(s)
    if typ == INTSXP or typ == LGLSXP:
        return POINTER(c_int)
    elif typ == REALSXP:
        return POINTER(c_double)
    elif typ == CHARSXP:
        return c_char_p
    return c_void_p


def dataptr(s):
    """
    DATAPTR is not exported, it is a trick to get the actual data.
    """
    return cast(s.value + rinstance.offset, dataptr_type(s))


def vector_elt(s, i):
    return rccall("VECTOR_ELT", c_void_p, [c_void_p, c_int], s, i)


def string_elt(s, i):
    return rccall("STRING_ELT", c_void_p, [c_void_p, c_int], s, i)


def try_eval(s, env=None):
    status = c_int()
    if not env:
        env = rcglobal("R_GlobalEnv")
    protect(env)
    val = rccall(
        "R_tryEval",
        c_void_p,
        [c_void_p, c_void_p, POINTER(c_int)],
        s,
        env,
        status)
    unprotect(1)
    return val, status.value


def lang1(s):
    return rccall("Rf_lang1", c_void_p, [c_void_p], s)


def lang2(s1, s2):
    return rccall("Rf_lang2", c_void_p, [c_void_p, c_void_p], s1, s2)


def lang3(s1, s2, s3):
    return rccall("Rf_lang2", c_void_p, [c_void_p, c_void_p, c_void_p], s1, s2, s3)


def lang4(s1, s2, s3, s4):
    return rccall(
        "Rf_lang2",
        c_void_p,
        [c_void_p, c_void_p, c_void_p, c_void_p],
        s1, s2, s3, s4)


def typeof(s):
    return rccall("TYPEOF", c_int, [c_void_p], s)


def alloc_vector(m, n):
    return rccall("Rf_allocVector", c_void_p, [c_int, c_int], m, n)


def cdr(s):
    return rccall("CDR", c_void_p, [c_void_p], s)


def car(s):
    return rccall("CAR", c_void_p, [c_void_p], s)


def tag(s):
    return rccall("TAG", c_void_p, [c_void_p], s)


def setcdr(s, t):
    return rccall("SETCDR", c_void_p, [c_void_p, c_void_p], s, t)


def setcar(s, t):
    return rccall("SETCAR", c_void_p, [c_void_p, c_void_p], s, t)


def settag(s, t):
    return rccall("SET_TAG", c_void_p, [c_void_p, c_void_p], s, t)


def print_value(s):
    rccall("Rf_PrintValue", None, [c_void_p], s)


def visible():
    return rcglobal("R_Visible", c_int)
