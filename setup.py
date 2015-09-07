from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import numpy

# extensions = [Extension("shift",["shift.pyx"], include_dirs = ["/usr/local/lib/python2.7/site-packages/numpy/core/include/"])];

setup(
	name = 'Shift utility',
	# ext_modules = cythonize(extensions),
	ext_modules = cythonize("shift.pyx", include_path=[numpy.get_include()]),
	include_dirs=[numpy.get_include()]
)

