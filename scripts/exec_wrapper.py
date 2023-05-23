#!/usr/bin/env python3

# Import as few modules and define as few names as possible at module level before exec'ing the
# file, as all names will be seen by the exec'ed code.  To prevent name collisions, all names
# defined or imported here at module level should begin with 'exec_wrapper_'

def exec_wrapper_get_colors():
	import os
	from collections import namedtuple
	return namedtuple('colors',['red','green','yellow','blue','purple'])(*[
			(lambda s:s) if os.getenv('MMGEN_DISABLE_COLOR') else
			(lambda s,n=n:f'\033[{n};1m{s}\033[0m' )
		for n in (31,32,33,34,35) ])

def exec_wrapper_init():

	import os
	if os.path.dirname(exec_wrapper_sys.argv[1]) == 'test': # scripts in ./test do overlay setup themselves
		exec_wrapper_sys.path[0] = 'test'
	else:
		from test.overlay import overlay_setup
		exec_wrapper_sys.path[0] = overlay_setup(repo_root=os.getcwd()) # assume we're in the repo root

	if 'TMUX' in os.environ:
		del os.environ['TMUX']

	if os.getenv('EXEC_WRAPPER_TRACEBACK'):
		try:
			os.unlink('test.py.err')
		except:
			pass

	os.environ['MMGEN_EXEC_WRAPPER'] = '1'

def exec_wrapper_write_traceback(e,exit_val):

	exc_line = (
		repr(e) if type(e).__name__ in ('MMGenError','MMGenSystemExit') else
		'{}: {}'.format( type(e).__name__, e ))
	c = exec_wrapper_get_colors()

	import os
	if os.getenv('EXEC_WRAPPER_TRACEBACK'):
		import traceback

		cwd = os.path.abspath('.')
		def fixup_fn(fn_in):
			from mmgen.util2 import removeprefix,removesuffix
			fn = removeprefix(removeprefix(fn_in,cwd+'/'),'test/overlay/tree/')
			return removesuffix(fn,'_orig.py') + '.py' if fn.endswith('_orig.py') else fn
			# Python 3.9:
			# fn = fn_in.removeprefix(cwd+'/').removeprefix('test/overlay/tree/')
			# return fn.removesuffix('_orig.py') + '.py' if fn.endswith('_orig.py') else fn

		def gen_output():
			yield 'Traceback (most recent call last):'
			for e in traceback.extract_tb(exec_wrapper_sys.exc_info()[2]):
				yield '  File "{f}", line {l}, in {n}\n    {L}'.format(
					f = exec_wrapper_execed_file if e.filename == '<string>' else fixup_fn(e.filename),
					l = '(scrubbed)' if os.getenv('MMGEN_TEST_SUITE_DETERMINISTIC') else e.lineno,
					n = e.name,
					L = e.line or 'N/A' )

		tb_lines = list( gen_output() )

		if 'SystemExit' in exc_line:
			tb_lines.pop()

		exec_wrapper_sys.stdout.write('{}\n{}\n'.format( c.yellow( '\n'.join(tb_lines) ), c.red(exc_line) ))

		with open('test.py.err','w') as fp:
			fp.write('\n'.join(tb_lines + [exc_line]))
	else:
		exec_wrapper_sys.stdout.write( c.purple((f'NONZERO_EXIT[{exit_val}]: ' if exit_val else '') + exc_line) + '\n' )

def exec_wrapper_end_msg():
	import os
	if os.getenv('EXEC_WRAPPER_SPAWN') and not os.getenv('MMGEN_TEST_SUITE_DETERMINISTIC'):
		c = exec_wrapper_get_colors()
		# write to stdout to ensure script output gets to terminal first
		import time
		exec_wrapper_sys.stdout.write(c.blue('Runtime: {:0.5f} secs\n'.format(time.time() - exec_wrapper_tstart)))

def exec_wrapper_tracemalloc_setup():
	import os
	if os.getenv('MMGEN_TRACEMALLOC'):
		os.environ['PYTHONTRACEMALLOC'] = '1'
		import tracemalloc
		tracemalloc.start()
		exec_wrapper_sys.stderr.write("INFO → Appending memory allocation stats to 'tracemalloc.log'\n")

def exec_wrapper_tracemalloc_log():
	import os
	if os.getenv('MMGEN_TRACEMALLOC'):
		import tracemalloc,re
		snapshot = tracemalloc.take_snapshot()
		stats = snapshot.statistics('lineno')
		depth = 100
		col1w = 100
		with open('tracemalloc.log','a') as fp:
			fp.write('##### TOP {} {} #####\n'.format(depth,' '.join(exec_wrapper_sys.argv)))
			for stat in stats[:depth]:
				frame = stat.traceback[0]
				fn = re.sub(r'.*\/site-packages\/|.*\/mmgen\/test\/overlay\/tree\/','',frame.filename)
				fn = re.sub(r'.*\/mmgen\/test\/','test/',fn)
				fp.write('{f:{w}} {s:>8.2f} KiB\n'.format(
					f = f'{fn}:{frame.lineno}:',
					s = stat.size/1024,
					w = col1w ))
			fp.write('{f:{w}} {s:8.2f} KiB\n\n'.format(
				f = 'TOTAL {}:'.format(' '.join(exec_wrapper_sys.argv))[:col1w],
				s = sum(stat.size for stat in stats) / 1024,
				w = col1w ))

def exec_wrapper_get_tstart():
	import time
	return time.time()

import sys as exec_wrapper_sys

exec_wrapper_init() # sets sys.path[0], runs overlay_setup()
exec_wrapper_tracemalloc_setup()

# import mmgen mods only after overlay setup!
from mmgen.devinit import init_dev as exec_wrapper_init_dev
exec_wrapper_init_dev()

exec_wrapper_tstart = exec_wrapper_get_tstart()

try:
	exec_wrapper_sys.argv.pop(0)
	exec_wrapper_execed_file = exec_wrapper_sys.argv[0]
	with open(exec_wrapper_execed_file) as fp:
		exec(fp.read())
except SystemExit as e:
	if e.code != 0:
		exec_wrapper_write_traceback(e,e.code)
	else:
		exec_wrapper_tracemalloc_log()
		exec_wrapper_end_msg()
	exec_wrapper_sys.exit(e.code)
except Exception as e:
	exit_val = e.mmcode if hasattr(e,'mmcode') else e.code if hasattr(e,'code') else 1
	exec_wrapper_write_traceback(e,exit_val)
	exec_wrapper_sys.exit(exit_val)

exec_wrapper_tracemalloc_log()
exec_wrapper_end_msg()
