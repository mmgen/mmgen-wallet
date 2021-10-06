#!/usr/bin/env python3

"""
Clean up control characters and trailing whitespace in the listed source files
and create a unified diff between them.

If more or less than two files are listed on the command line, the cleanup is
performed on all files, but no diff is created.

The source files are assumed to be terminal output captured by the `script`
command.

The original source files are backed up with the .orig extension.
"""

import sys,re
from difflib import unified_diff

fns = sys.argv[1:]

translate = {
	'\r': '[CR]\n',
	'\b': '[BS]',
}

def cleanup_file(fn):
	data = open(fn).read()
	def gen_text():
		for line in data.splitlines():
			line = re.sub('\r\n','\n',line) # DOS CRLF to Unix LF
			line = line.translate({ord(a):b for a,b in translate.items()})
			line = re.sub(r'\s+$','',line)  # trailing whitespace
			yield line
	ret = list(gen_text())
	open(fn+'.orig','w').write(data)
	open(fn,'w').write('\n'.join(ret))
	return ret

cleaned_texts = [cleanup_file(fn) for fn in fns]

if len(fns) == 2:
	print('\n'.join(unified_diff(*cleaned_texts)))
else:
	print(f'{len(fns)} input files.  Not generating diff.')
