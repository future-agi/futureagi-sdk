"""Source for a fresh interpreter: ``is_stdlib(name)``, whether a loaded top-level module is the standard library's.

``sys.stdlib_module_names`` decides on 3.10+. On 3.9 (``futureagi-webhooks`` supports it) a module counts as standard
only when it is built in or frozen, or its file lies under the interpreter's stdlib directories and outside
site-packages; a namespace package or a module with no known file does not count.
"""

IS_STDLIB = '''
def is_stdlib(name):
    import sys
    names = getattr(sys, "stdlib_module_names", None)
    if names is not None:
        return name in names
    import os, sysconfig
    mod = sys.modules.get(name)
    origin = getattr(getattr(mod, "__spec__", None), "origin", None)
    if name in sys.builtin_module_names or origin in ("built-in", "frozen"):
        return True
    path = getattr(mod, "__file__", None) or origin
    if not path or "site-packages" in path:
        return False
    path = os.path.realpath(path)
    roots = {os.path.realpath(sysconfig.get_paths()[k]) + os.sep for k in ("stdlib", "platstdlib")}
    return any(path.startswith(root) for root in roots)
'''
