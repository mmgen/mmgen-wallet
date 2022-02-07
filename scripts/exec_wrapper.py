#!/usr/bin/env python3

# Import as few modules and define as few names as possible at global level before exec'ing the
# file, as all names will be seen by the exec'ed code.  To prevent name collisions, all names
# defined here should begin with 'exec_wrapper_'

import sys,os,time

def exec_wrapper_get_colors():
	from collections import namedtuple
	return namedtuple('colors',['red','green','yellow','blue'])(*[
			(lambda s:s) if os.getenv('MMGEN_DISABLE_COLOR') else
			(lambda s,n=n:f'\033[{n};1m{s}\033[0m' )
		for n in (31,32,33,34) ])

def exec_wrapper_init(): # don't change: name is used to test if script is running under exec_wrapper

	if os.path.dirname(sys.argv[1]) == 'test': # scripts in ./test do overlay setup themselves
		sys.path[0] = 'test'
	else:
		from test.overlay import overlay_setup
		sys.path[0] = overlay_setup(repo_root=os.getcwd()) # assume we're in the repo root

	os.environ['MMGEN_EXEC_WRAPPER'] = '1'
	os.environ['PYTHONPATH'] = '.'
	if 'TMUX' in os.environ:
		del os.environ['TMUX']

	if not os.getenv('EXEC_WRAPPER_NO_TRACEBACK'):
		try:
			os.unlink('test.py.err')
		except:
			pass

def exec_wrapper_write_traceback(e):
	import traceback,re
	lines = traceback.format_exception(*sys.exc_info()) # returns a list

	pat = re.compile('File "<string>"')
	repl = f'File "{exec_wrapper_execed_file}"'
	lines = [pat.sub(repl,line,count=1) for line in lines]

	exc = lines.pop()
	if exc.startswith('SystemExit:'):
		lines.pop()

	if os.getenv('MMGEN_TEST_SUITE_DETERMINISTIC'):
		pat = re.compile(", line [0-9]+,")
		lines = [pat.sub(", line (scrubbed),",line) for line in lines]

	c = exec_wrapper_get_colors()
	message = ( repr(e) if type(e).__name__ in ('MMGenError','MMGenSystemExit') else exc )
	sys.stdout.write('{}{}'.format(
		c.yellow( ''.join(lines) ),
		c.red(message) )
	+ '\n' )

	if not os.getenv('EXEC_WRAPPER_NO_TRACEBACK'):
		with open('test.py.err','w') as fp:
			fp.write(''.join(lines+[exc]))

def exec_wrapper_end_msg():
	if os.getenv('EXEC_WRAPPER_SPAWN') and not os.getenv('MMGEN_TEST_SUITE_DETERMINISTIC'):
		c = exec_wrapper_get_colors()
		# write to stdout to ensure script output gets to terminal first
		sys.stdout.write(c.blue('Runtime: {:0.5f} secs\n'.format(time.time() - exec_wrapper_tstart)))

def exec_wrapper_tracemalloc_setup():
	if os.getenv('MMGEN_TRACEMALLOC'):
		os.environ['PYTHONTRACEMALLOC'] = '1'
		import tracemalloc
		tracemalloc.start()
		sys.stderr.write("INFO → Appending memory allocation stats to 'tracemalloc.log'\n")

def exec_wrapper_tracemalloc_log():
	if os.getenv('MMGEN_TRACEMALLOC'):
		import tracemalloc,re
		snapshot = tracemalloc.take_snapshot()
		stats = snapshot.statistics('lineno')
		depth = 100
		col1w = 100
		with open('tracemalloc.log','a') as fp:
			fp.write('##### TOP {} {} #####\n'.format(depth,' '.join(sys.argv)))
			for stat in stats[:depth]:
				frame = stat.traceback[0]
				fn = re.sub(r'.*\/site-packages\/|.*\/mmgen\/test\/overlay\/tree\/','',frame.filename)
				fn = re.sub(r'.*\/mmgen\/test\/','test/',fn)
				fp.write('{f:{w}} {s:>8.2f} KiB\n'.format(
					f = f'{fn}:{frame.lineno}:',
					s = stat.size/1024,
					w = col1w ))
			fp.write('{f:{w}} {s:8.2f} KiB\n\n'.format(
				f = 'TOTAL {}:'.format(' '.join(sys.argv))[:col1w],
				s = sum(stat.size for stat in stats) / 1024,
				w = col1w ))

exec_wrapper_init() # sets sys.path[0]
exec_wrapper_tstart = time.time()
exec_wrapper_tracemalloc_setup()

try:
	sys.argv.pop(0)
	exec_wrapper_execed_file = sys.argv[0]
	with open(exec_wrapper_execed_file) as fp:
		exec(fp.read())
except SystemExit as e:
	if e.code != 0 and not os.getenv('EXEC_WRAPPER_NO_TRACEBACK'):
		exec_wrapper_write_traceback(e)
	else:
		exec_wrapper_tracemalloc_log()
		exec_wrapper_end_msg()
	sys.exit(e.code)
except Exception as e:
	if not os.getenv('EXEC_WRAPPER_NO_TRACEBACK'):
		exec_wrapper_write_traceback(e)
	retval = e.mmcode if hasattr(e,'mmcode') else e.code if hasattr(e,'code') else 1
	sys.exit(retval)

exec_wrapper_tracemalloc_log()
exec_wrapper_end_msg()
