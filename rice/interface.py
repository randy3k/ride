from __future__ import unicode_literals
from collections import OrderedDict
from . import api
"""
High level functions to interact with R api.
"""


def get_option(key, default=None):
    s = rcall(api.mk_symbol("options"), api.mk_string(key))
    ret = rcopy(api.vector_elt(s, 0), simplify=True)
    if not ret:
        ret = default
    return ret


def r_version():
    info = rcopy(rcall(api.mk_symbol("R.Version")), simplify=True)
    return "{} -- {}\nPlatform: {}\n".format(
        info["version.string"], info["nickname"], info["platform"])


def installed_packages():
    return rcopy(reval("row.names(installed.packages())"))


def rcopy(s, simplify=False):
    api.protect(s)
    ret = None
    typ = api.typeof(s)
    if typ == api.VECSXP:
        ret = OrderedDict()
        names = rcopy(rcall(api.mk_symbol("names"), s))
        for i in range(api.length(s)):
            ret[names[i]] = rcopy(api.vector_elt(s, i), simplify=simplify)
    elif typ == api.STRSXP:
        ret = []
        for i in range(api.length(s)):
            ret.append(api.dataptr(api.string_elt(s, i)).value.decode("utf-8"))
        if simplify and len(ret) == 1:
            ret = ret[0]
    elif typ == api.LGLSXP or api.INTSXP or api.REALSXP:
        ret = []
        sp = api.dataptr(s)
        for i in range(api.length(s)):
            ret.append(sp[i])
        if simplify and len(ret) == 1:
            ret = ret[0]
    api.unprotect(1)
    return ret


def rlang(*args, **kwargs):
    nargs = len(args) + len(kwargs)
    t = api.protect(api.alloc_vector(api.LANGSXP, nargs))
    s = t
    api.setcar(s, args[0])
    for a in args[1:]:
        s = api.cdr(s)
        api.setcar(s, a)
    for k, v in kwargs.items():
        s = api.cdr(s)
        api.setcar(s, v)
        api.settag(s, api.mk_symbol(k))
    api.unprotect(1)
    return t


def rcall(*args, **kwargs):
    val, status = api.try_eval(rlang(*args, **kwargs))
    if status != 0:
        raise RuntimeError("R eval error.")
    return val


def rparse(s):
    val, status = api.parse_vector(api.mk_string(s))
    if status != 1:
        raise SyntaxError("Error: %s" % api.parse_error_msg())
    return val


def reval(s):
    try:
        exprs = rparse(s)
    except Exception as e:
        raise e
    api.protect(exprs)
    val = None
    try:
        for i in range(0, api.length(exprs)):
            val, status = api.try_eval(api.vector_elt(exprs, i))
            if status != 0:
                raise RuntimeError("R eval error.")
    finally:
        api.unprotect(1)  # exprs
    return val


def rprint(s):
    api.protect(s)
    try:
        rcall(api.mk_symbol("print"), s)
    finally:
        api.unprotect(1)


def help(topic):
    result = rcall(api.mk_symbol("help"), api.mk_symbol(topic))
    rprint(result)


def help_search(topic, try_all_packages=False):
    result = rcall(api.mk_symbol("help.search"), api.mk_string(topic))
    rprint(result)
