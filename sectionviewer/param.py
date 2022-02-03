import os
import platform

svdir = os.path.dirname(os.path.abspath(__file__))
def svp(relat):
    return os.path.join(svdir, relat)

pf = platform.system()