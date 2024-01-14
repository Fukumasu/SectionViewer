from glob import glob
from os.path import basename, splitext
import platform
from setuptools import setup, Extension

def build_ext(*args, **kwargs):
    from Cython.Distutils import build_ext as build_ext_cy
    class _build_ext(build_ext_cy):
        def finalize_options(self):
            build_ext_cy.finalize_options(self)
            __builtins__.__NUMPY_SETUP__ = False
            import numpy
            self.include_dirs.append(numpy.get_include())
    return _build_ext(*args, **kwargs)

install_requires = open('requirements.txt').read().splitlines()

pf = platform.system()
if pf == 'Windows':
    omp = '/openmp'
    pd = ['*.txt', '*.pyx', 'img/resources.png', 'img/icon.ico']
elif pf == 'Darwin':
    omp = ''
    pd = ['*.txt', '*.pyx', 'img/resources.png']
elif pf == 'Linux':
    omp = '-fopenmp'
    pd = ['*.txt', '*.pyx', 'img/resources.png']

ext_modules = [Extension('sectionviewer.utils', 
                         sources = ['sectionviewer/utils.pyx'],
                         extra_compile_args = [omp],
                         extra_link_args = [omp]
                        )
              ]
cmdclass = {'build_ext': build_ext}

info = open('info.txt').read()
exec(info)
open('sectionviewer/info.py', 'w').write(info)

setup(
    name = 'sectionviewer',
    version = version,
    packages = ['sectionviewer', 'sectionviewer.gui', 
                'sectionviewer.img', 'sectionviewer.temp'],
    ext_modules = ext_modules,
    cmdclass=cmdclass,
    install_requires = install_requires,
    py_modules=[splitext(basename(path))[0]
                for path in glob('sectionviewer/*.py') + glob('sectionviewer/gui/*.py')],
    package_data = {'': pd},
    include_package_data = True,
    setup_requires = ['numpy', 'cython'],
    entry_points = {
        'console_scripts': [
            'sectionviewer = sectionviewer.main:main'
        ]
    }
)
