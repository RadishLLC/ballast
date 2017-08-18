import sys


PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2
PY26 = sys.version_info[0:2] == (2, 6)
PY27 = sys.version_info[0:2] == (2, 7)
PYPY = hasattr(sys, 'pypy_translation_info')


if PY3:

    def cmp(x, y):
        """
        cmp(x, y) -> integer

        Return negative if x<y, zero if x==y, positive if x>y.
        """
        return (x > y) - (x < y)

    unicode = str
    basestring = str
    unichr = chr
    xrange = range
else:
    import __builtin__
    cmp = __builtin__.cmp
    unicode = __builtin__.unicode
    basestring = __builtin__.basestring
    unichr = __builtin__.unichr
    xrange = __builtin__.xrange
