from distutils.core import setup
from Cython.Build import cythonize
import Cython.Compiler.Options

Cython.Compiler.Options.cimport_from_pyx = True

setup(
	ext_modules=cythonize(
		[
			"src/chunk/__init__.pyx",
			"src/chunk/chunk.pyx",
			"src/chunk/subchunk.pyx",
		],
		compiler_directives={
			"language_level": 3,
			"profile": True,
		},
		annotate=True,
	)
)
