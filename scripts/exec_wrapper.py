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

def exec_wrapper_init():

	sys.path[0] = 'test' if os.path.dirname(sys.argv[1]) == 'test' else '.'

	os.environ['MMGEN_TRACEBACK'] = '1'
	os.environ['PYTHONPATH'] = '.'
	if 'TMUX' in os.environ:
		del os.environ['TMUX']

	of = 'my.err'
	try: os.unlink(of)
	except: pass

	return of

def exec_wrapper_write_traceback():
	import traceback,re
	lines = traceback.format_exception(*sys.exc_info()) # returns a list

	pat = re.compile('File "<string>"')
	repl = f'File "{exec_wrapper_execed_file}"'
	lines = [pat.sub(repl,line,count=1) for line in lines]

	exc = lines.pop()
	if exc.startswith('SystemExit:'):
		lines.pop()

	c = exec_wrapper_get_colors()
	sys.stdout.write('{}{}'.format(c.yellow(''.join(lines)),c.red(exc)))

	open(exec_wrapper_traceback_file,'w').write(''.join(lines+[exc]))

exec_wrapper_traceback_file = exec_wrapper_init() # sets sys.path[0]
exec_wrapper_tstart = time.time()

try:
	sys.argv.pop(0)
	exec_wrapper_execed_file = sys.argv[0]
	exec(open(sys.argv[0]).read())
except SystemExit as e:
	if e.code != 0:
		exec_wrapper_write_traceback()
	sys.exit(e.code)
except Exception as e:
	exec_wrapper_write_traceback()
	retval = e.mmcode if hasattr(e,'mmcode') else e.code if hasattr(e,'code') else 1
	sys.exit(retval)

c = exec_wrapper_get_colors()
sys.stderr.write(c.blue('Runtime: {:0.5f} secs\n'.format(time.time() - exec_wrapper_tstart)))
