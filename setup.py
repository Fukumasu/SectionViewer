from glob import glob
from os.path import basename, splitext
import platform
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext as _build_ext

class build_ext(_build_ext):
  def finalize_options(self):
    _build_ext.finalize_options(self)
    __builtins__.__NUMPY_SETUP__ = False
    import numpy
    self.include_dirs.append(numpy.get_include())

ext_modules = [Extension('sectionviewer.utils', 
                         sources=['sectionviewer/utils.c'],
                         extra_compile_args=['/openmp'],
                         extra_link_args=['/openmp'])]
cmdclass = {'build_ext': build_ext}

def _requires_from_file(filename):
    return open(filename).read().splitlines()

pf = platform.system()
if pf == "Windows":
    setup(
        name = 'sectionviewer',
        version = '1.0.0',
        packages=['sectionviewer'],
        ext_modules=ext_modules,
        cmdclass=cmdclass,
        install_requires=_requires_from_file('requirements.txt'),
        py_modules=[splitext(basename(path))[0] for path in glob('sectionviewer/*.py')],
        package_data={'': ['*.txt', "*.pyx", 'img/resources.png', 'img/SectionViewer.ico', 'subdir/launcher.py']},
        include_package_data=True,
        setup_requires=['numpy'],
        entry_points = {
            'console_scripts': [
                'sectionviewer = sectionviewer.sectionviewer:main'
            ]
        }
    )
