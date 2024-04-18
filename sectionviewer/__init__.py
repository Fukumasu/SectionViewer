from .core import load
from .tools import launch, check_version
from .info import version, url

__version__ = version

v = check_version()
if v:
    print('Version {0} is now available! Please check <{1}>.'.format(v, url))
