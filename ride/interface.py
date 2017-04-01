from ctypes import c_char
from collections import OrderedDict
from . import api

"""
High level functions to interact with R api.
"""


def r_version_list():
    return {k: v[0] for (k, v) in rcopy(rcall(api.mk_symbol("R.Version"))).items()}


def r_version():
    info = r_version_list()
    return "{} -- {}\nPlatform: {}\n".format(
        info["version.string"], info["nickname"], info["platform"])


def rcopy(s):
    api.protect(s)
    ret = None
    typ = api.typeof(s)
    if typ == api.VECSXP:
        ret = OrderedDict()
        names = rcopy(rcall(api.mk_symbol("names"), s))
        for i in range(api.length(s)):
            ret[names[i]] = rcopy(api.vector_elt(s, i))
    elif typ == api.STRSXP:
        ret = []
        for i in range(api.length(s)):
            ret.append(api.dataptr(api.string_elt(s, i)).value.decode("utf-8"))
    elif typ == api.LGLSXP or api.INTSXP or api.REALSXP:
        ret = []
        sp = api.dataptr(s)
        for i in range(api.length(s)):
            ret.append(sp[i])
    api.unprotect(1)
    return ret


def rlang(*args, **kwargs):
    nargs = len(args) + len(kwargs)
    s = l = api.protect(api.alloc_vector(api.LANGSXP, nargs))
    api.setcar(s, args[0])
    for a in args[1:]:
        s = api.cdr(s)
        api.setcar(s, a)
    for k, v in kwargs.items():
        s = api.cdr(s)
        api.setcar(s, v)
        api.settag(s, api.mk_symbol(k))
    api.unprotect(1)
    return l


def rcall(*args, **kwargs):
    val, status = api.try_eval(rlang(*args, **kwargs))
    if status != 0:
        raise RuntimeError("R eval error.")
    return val


def rparse(s):
    val, status = api.parse_vector(api.mk_string(s))
    if status != 1:
        raise SyntaxError("R has a parser error %d." % status)
    return val


def reval(s):
    try:
        exprs = rparse(s)
    except Exception as e:
        raise e
    api.protect(exprs)
    try:
        for i in range(0, api.length(exprs)):
            val, status = api.try_eval(api.vector_elt(exprs, i))
            if status != 0:
                raise RuntimeError("R eval error.")
    finally:
        api.unprotect(1)  # exprs
    return val


def rprint(s):
    rcall(api.mk_symbol("print"), s)