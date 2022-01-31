from distutils.core import setup, Extension
from Cython.Build import cythonize
from numpy import get_include

ext = Extension("utils", sources=["utils.pyx"], extra_compile_args=["/openmp"],
                include_dirs=[".", get_include()])
setup(name="utils", ext_modules=cythonize([ext], compiler_directives={"language_level": "3"}))
