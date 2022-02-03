import os
import platform

svdir = os.path.dirname(os.path.abspath(__file__))
def svp(relat):
    return os.path.join(svdir, relat)

pf = platform.system()
if pf == 'Windows':    
    icon_path = svp('img/icon.ico')
elif pf == 'Darwin':
    icon_path = svp('img/icon.icns')
elif pf == 'Linux':
    icon_path = svp('img/icon.xbm')
