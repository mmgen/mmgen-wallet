#!/usr/bin/env python3

"""
scripts/gendiff.py:

Clean up control characters and trailing whitespace in the listed source files
and create a unified diff between them.

If more or less than two files are listed on the command line, the cleanup is
performed on all files, but no diff is created.

The source files are assumed to be terminal output captured by the `script`
command.

The cleaned source files are saved with the .clean extension.
"""

import sys, re
from difflib import unified_diff

fns = sys.argv[1:3]
diff_opts = sys.argv[4:] if sys.argv[3:4] == ['--'] else None

translate = {
	'\r': None,
	'\b': '[BS]',
#	chr(4): '', # Ctrl-D, EOT
}

def cleanup_file(fn):

	# must use binary mode to prevent conversion of DOS CR into newline
	with open(fn, 'rb') as fp:
		data = fp.read().decode()

	def gen_text():
		for line in data.split('\n'): # do not use splitlines()
			line = line.translate({ord(a): b for a, b in translate.items()})
			line = re.sub(r'\s+$', '', line)  # trailing whitespace
			yield line

	ret = list(gen_text())

	sys.stderr.write(f'Saving cleaned file to {fn}.clean\n')

	with open(f'{fn}.clean', 'w') as fp:
		fp.write('\n'.join(ret))

	return ret

if len(fns) != 2:
	sys.stderr.write(f'{len(fns)} input files.  Not generating diff.\n')

cleaned_texts = [cleanup_file(fn) for fn in fns]

if len(fns) == 2:
	# chunk headers have trailing newlines, hence the rstrip()
	sys.stderr.write('Generating diff\n')
	if diff_opts:
		from subprocess import run
		run(['diff', '-u'] + [f'{fn}.clean' for fn in fns])
	else:
		print(
			f'diff a/{fns[0]} b/{fns[1]}\n' +
			'\n'.join(a.rstrip() for a in unified_diff(
				*cleaned_texts,
				fromfile = f'a/{fns[0]}',
				tofile   = f'b/{fns[1]}'))
		)
