import os

import pylint.lint as linter

print("Starting linter...")

LINTER_OPTIONS = [
	"--disable", "C0114", # disable 'missing-module-docstring'
	"--disable", "C0115", # disable 'missing-class-docstring'
	"--disable", "C0116", # disable 'missing-function-docstring'
	"--disable", "R0801", # disable 'duplicate-code' (there's naturally gonna be duplicate code between episodes)
	"--disable", "W0311", # TIL some "people" unironically prefer spaces to tabs 🤮
]

files = ["./lint.py", "./community"]

for path in os.listdir("."):
	if "episode-" in path:
		files.append(path)

results = linter.Run(files + LINTER_OPTIONS, do_exit = False)
score = results.linter.stats.global_note

if score < 10:
	raise Exception(f"Linter failed; score is {score}")
