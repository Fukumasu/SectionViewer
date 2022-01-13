from glob import glob
from os.path import basename, splitext
import platform
from setuptools import setup, Extension, find_packages

def _requires_from_file(filename):
    return open(filename).read().splitlines()

pf = platform.system()
if pf == "Windows":
    setup(
        name = 'sectionviewer',
        version = '1.0.0',
        packages=['windows'],
        install_requires=_requires_from_file('requirements.txt'),
        py_modules=[splitext(basename(path))[0] for path in glob('windows/*.py')],
        package_data={'': ['*.exe', '*.dll', 'img/resources.zip', 'img/SectionViewer.ico']},
        include_package_data=True,
        entry_points = {
            'console_scripts': [
                'sectionviewer = windows.sectionviewer:main'
            ]
        }
    )
