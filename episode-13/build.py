from setuptools.command.build_ext import build_ext
from Cython.Build import cythonize
import Cython.Compiler.Options

Cython.Compiler.Options.cimport_from_pyx = True  # needed?


class BuildExt(build_ext):
	def build_extension(self, ext):
		self.inplace = True  # Important or the LSP won't have access to the compiled files.
		super().build_extension(ext)


def build(setup_kwargs):
	ext_modules = cythonize(
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

	setup_kwargs.update({"ext_modules": ext_modules, "cmdclass": {"build_ext": BuildExt}})
