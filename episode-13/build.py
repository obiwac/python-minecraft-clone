from setuptools.command.build_ext import build_ext
from Cython.Build import cythonize
import Cython.Compiler.Options

Cython.Compiler.Options.cimport_from_pyx = True  # needed?

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


class ExtBuilder(build_ext):
	def run(self):
		build_ext.run(self)

	def build_extension(self, ext):
		build_ext.build_extension(self, ext)


def build(setup_kwargs):
	setup_kwargs.update({"ext_modules": ext_modules, "cmdclass": {"build_ext": ExtBuilder}})
