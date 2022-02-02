from glob import glob
from os.path import basename, splitext
import platform
from setuptools import setup, Extension, find_packages

version = '1.0.0'

info = \
'''
version = '{0}'
author = 'Kazushi Fukumasu'
url = 'https://github.com/Fukumasu/SectionViewer'
upgrade_code = '\{6bd9a5e4-428c-4053-8956-9c452ebeefcf\}'
'''.format(version)
with open('sectionviewer/info.py', 'w') as f:
    f.write(info)

def build_ext(*args, **kwargs):
    from Cython.Distutils import build_ext as build_ext_cy
    class _build_ext(build_ext_cy):
        def finalize_options(self):
            build_ext_cy.finalize_options(self)
            __builtins__.__NUMPY_SETUP__ = False
            import numpy
            self.include_dirs.append(numpy.get_include())
    return _build_ext(*args, **kwargs)

pf = platform.system()
if pf == 'Windows':
    omp = '/openmp'
    icon = 'img/SectionViewer.ico'
elif pf == 'Darwin':
    omp = '-fopenmp'
    icon = 'img/SectionViewer.icns'
else:
    omp = '-fopenmp'
    icon = 'img/SectionViewer.ico'

ext_modules = [Extension('sectionviewer.utils', 
                         sources=['sectionviewer/utils.pyx'],
                         extra_compile_args=[omp],
                         extra_link_args=[omp])]
cmdclass = {'build_ext': build_ext}

def _requires_from_file(filename):
    return open(filename).read().splitlines()

setup(
    name = 'sectionviewer',
    version = version,
    packages=['sectionviewer'],
    ext_modules=ext_modules,
    cmdclass=cmdclass,
    install_requires=_requires_from_file('requirements.txt'),
    py_modules=[splitext(basename(path))[0] for path in glob('sectionviewer/*.py')],
    package_data={'': ['*.txt', "*.pyx", 'img/*.png', icon, 'subdir/launcher.py']},
    include_package_data=True,
    setup_requires=['numpy', 'cython'],
    entry_points = {
        'console_scripts': [
            'sectionviewer = sectionviewer.sectionviewer:launch'
        ]
    }
)
