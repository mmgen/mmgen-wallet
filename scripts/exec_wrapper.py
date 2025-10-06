#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
scripts/exec_wrapper.py: wrapper to launch MMGen scripts in a testing environment
"""

# Import as few modules and define as few names as possible at module level before exec'ing the
# file, as all names will be seen by the exec'ed code.  To prevent name collisions, all names
# defined or imported here at module level should begin with 'exec_wrapper_'

def exec_wrapper_get_colors():
	from collections import namedtuple
	return namedtuple('colors', ['red', 'green', 'yellow', 'blue', 'purple'])(*[
			(lambda s: s) if exec_wrapper_os.getenv('MMGEN_DISABLE_COLOR') else
			(lambda s, n=n: f'\033[{n};1m{s}\033[0m')
		for n in (31, 32, 33, 34, 35)])

def exec_wrapper_init():

	if exec_wrapper_os.path.dirname(exec_wrapper_sys.argv[1]) == 'test':
		# support running of test scripts under wrapper
		repo_root = exec_wrapper_os.getcwd() # assume we’re in repo root
		exec_wrapper_sys.path[0] = repo_root
		# ensure loading of mmgen mods from overlay tree, not repo root:
		from test.overlay import overlay_setup
		overlay_setup(repo_root)
	else:
		exec_wrapper_sys.path.pop(0)

	exec_wrapper_os.environ['MMGEN_EXEC_WRAPPER'] = '1'

def exec_wrapper_write_traceback(e, exit_val):

	import sys, os

	exc_line = (
		f'{type(e).__name__}({e.mmcode}) {e}' if type(e).__name__ in ('MMGenError', 'MMGenSystemExit') else
		f'{type(e).__name__}: {e}')

	c = exec_wrapper_get_colors()

	if os.getenv('EXEC_WRAPPER_TRACEBACK'):
		import traceback
		cwd = os.getcwd()
		sys.path.insert(0, cwd)
		from test.overlay import get_overlay_tree_dir
		overlay_path_pfx = os.path.relpath(get_overlay_tree_dir(cwd)) + '/'

		def fixup_fn(fn_in):
			fn = fn_in.removeprefix(cwd+'/').removeprefix(overlay_path_pfx)
			return fn.removesuffix('_orig.py') + '.py' if fn.endswith('_orig.py') else fn

		def gen_output():
			yield 'Traceback (most recent call last):'
			for e in traceback.extract_tb(sys.exc_info()[2]):
				yield '  File "{f}", line {l}, in {n}\n    {L}'.format(
					f = exec_wrapper_execed_file if e.filename == '<string>' else fixup_fn(e.filename),
					l = '(scrubbed)' if os.getenv('MMGEN_TEST_SUITE_DETERMINISTIC') else e.lineno,
					n = e.name,
					L = e.line or 'N/A')

		tb_lines = list(gen_output())

		if 'SystemExit' in exc_line:
			tb_lines.pop()

		if os.getenv('EXEC_WRAPPER_EXIT_VAL') == str(exit_val):
			sys.stdout.write(c.yellow(exc_line) + '\n')
		else:
			sys.stdout.write('{}\n{}\n'.format(
				c.yellow('\n'.join(tb_lines)),
				c.red(exc_line)))
			print(c.blue('{} script exited with error').format(
				'Test' if os.path.dirname(sys.argv[0]) == 'test' else 'Spawned'))

		with open('test.err', 'w') as fp:
			fp.write('\n'.join(tb_lines + [exc_line]))

	else:
		sys.stdout.write(c.purple((f'NONZERO_EXIT[{exit_val}]: ' if exit_val else '') + exc_line) + '\n')

def exec_wrapper_end_msg():
	if (
		exec_wrapper_os.getenv('EXEC_WRAPPER_DO_RUNTIME_MSG')
		and not exec_wrapper_os.getenv('MMGEN_TEST_SUITE_DETERMINISTIC')):
		c = exec_wrapper_get_colors()
		# write to stdout to ensure script output gets to terminal first
		exec_wrapper_sys.stdout.write(c.blue('Runtime: {:0.5f} secs\n'.format(
			exec_wrapper_time.time() - exec_wrapper_tstart)))

def exec_wrapper_tracemalloc_setup():
	exec_wrapper_os.environ['PYTHONTRACEMALLOC'] = '1'
	import tracemalloc
	tracemalloc.start()
	exec_wrapper_sys.stderr.write("INFO → Appending memory allocation stats to 'tracemalloc.log'\n")

def exec_wrapper_tracemalloc_log():
	import tracemalloc, re
	snapshot = tracemalloc.take_snapshot()
	stats = snapshot.statistics('lineno')
	depth = 100
	col1w = 100
	with open('tracemalloc.log', 'a') as fp:
		fp.write('##### TOP {} {} #####\n'.format(depth, ' '.join(exec_wrapper_sys.argv)))
		for stat in stats[:depth]:
			frame = stat.traceback[0]
			fn = re.sub(r'.*\/site-packages\/|.*\/mmgen\/test\/overlay\/tree\/', '', frame.filename)
			fn = re.sub(r'.*\/mmgen\/test\/', 'test/', fn)
			fp.write('{f:{w}} {s:>8.2f} KiB\n'.format(
				f = f'{fn}:{frame.lineno}:',
				s = stat.size/1024,
				w = col1w))
		fp.write('{f:{w}} {s:8.2f} KiB\n\n'.format(
			f = 'TOTAL {}:'.format(' '.join(exec_wrapper_sys.argv))[:col1w],
			s = sum(stat.size for stat in stats) / 1024,
			w = col1w))

def exec_wrapper_do_exit(e, exit_val):
	if exit_val != 0:
		exec_wrapper_write_traceback(e, exit_val)
	else:
		if exec_wrapper_os.getenv('MMGEN_TRACEMALLOC'):
			exec_wrapper_tracemalloc_log()
		exec_wrapper_end_msg()
	exec_wrapper_sys.exit(exit_val)

import sys as exec_wrapper_sys
import os as exec_wrapper_os
import time as exec_wrapper_time

exec_wrapper_init() # sets sys.path[0] to overlay root

if exec_wrapper_os.getenv('MMGEN_TRACEMALLOC'):
	exec_wrapper_tracemalloc_setup()

# import mmgen mods only after sys.path[0] is set to overlay root!
if exec_wrapper_os.getenv('MMGEN_DEVTOOLS'):
	from mmgen.devinit import init_dev as exec_wrapper_init_dev
	exec_wrapper_init_dev()

exec_wrapper_tstart = exec_wrapper_time.time()

try:
	exec_wrapper_sys.argv.pop(0)
	exec_wrapper_execed_file = exec_wrapper_sys.argv[0]
	with open(exec_wrapper_execed_file) as fp:
		exec(fp.read())
except SystemExit as e:
	exec_wrapper_do_exit(e, e.code)
except Exception as e:
	exec_wrapper_do_exit(
		e, e.mmcode if hasattr(e, 'mmcode') else e.code if hasattr(e, 'code') else 1)

if exec_wrapper_os.getenv('MMGEN_TRACEMALLOC'):
	exec_wrapper_tracemalloc_log()

exec_wrapper_end_msg()
