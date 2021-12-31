from glob import glob
from os.path import basename, splitext
from Cython.Distutils import build_ext
from setuptools import setup, Extension, find_packages
from numpy import get_include

def _requires_from_file(filename):
    return open(filename).read().splitlines()

ext_modules = [
    Extension('sectionviewer.util', 
              sources=['sectionviewer/util.pyx'],
              extra_compile_args=["/openmp"],
              extra_link_args=["/openmp"], 
              include_dirs=[".", get_include()])
]

setup(
    name = 'sectionviewer',
    version = '1.0.0',
    packages=['sectionviewer'],
    install_requires=_requires_from_file('requirements.txt'),
    py_modules=[splitext(basename(path))[0] for path in glob('sectionviewer/*.py')],
    package_data={'': ['*.exe', 'SectionViewer/*.exe', 'img/resources.zip']},
    include_package_data=True,
    ext_modules=ext_modules,
    cmdclass={'build_ext': build_ext},
    entry_points = {
        'gui_scripts': [
            'sectionviewer = sectionviewer.sectionviewer:main',
            'sectionviewer_desktop = sectionviewer.sectionviewer_desktop:main'
        ]
    }
)
