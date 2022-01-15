#!/usr/bin/env python3

"""
Clean up control characters and trailing whitespace in the listed source files
and create a unified diff between them.

If more or less than two files are listed on the command line, the cleanup is
performed on all files, but no diff is created.

The source files are assumed to be terminal output captured by the `script`
command.

The cleaned source files are saved with the .clean extension.
"""

import sys,re
from difflib import unified_diff

fns = sys.argv[1:]

translate = {
#	'\r': '[CR]\n',
	'\r': '',
	'\b': '[BS]',
#	chr(4): '', # Ctrl-D, EOT
}

def cleanup_file(fn):

	with open(fn) as fp:
		data = fp.read()

	def gen_text():
		for line in data.splitlines():
#			line = re.sub('\r\n','\n',line) # DOS CRLF to Unix LF
			line = line.translate({ord(a):b for a,b in translate.items()})
			line = re.sub(r'\s+$','',line)  # trailing whitespace
			yield line

	ret = list(gen_text())

	sys.stderr.write(f'Saving cleaned file to {fn}.clean\n')

	with open(f'{fn}.clean','w') as fp:
		fp.write('\n'.join(ret))

	return ret

if len(fns) != 2:
	sys.stderr.write(f'{len(fns)} input files.  Not generating diff.\n')

cleaned_texts = [cleanup_file(fn) for fn in fns]

if len(fns) == 2:
	"""
	chunk headers have trailing newlines, hence the rstrip()
	"""
	sys.stderr.write('Generating diff\n')
	print(
		f'diff a/{fns[0]} b/{fns[1]}\n' +
		'\n'.join(a.rstrip() for a in unified_diff(*cleaned_texts,fromfile=f'a/{fns[0]}',tofile=f'b/{fns[1]}'))
	)
