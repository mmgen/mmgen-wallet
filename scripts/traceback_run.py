#!/usr/bin/env python3

# Import as few modules and define as few names as possible at global level before exec'ing the
# file, as all names will be seen by the exec'ed file.  To prevent name collisions, all names
# defined here should begin with 'traceback_run_'

import sys,os,time

def traceback_run_init():
	import os
	sys.path[0] = 'test' if os.path.dirname(sys.argv[1]) == 'test' else '.'

	if 'TMUX' in os.environ: del os.environ['TMUX']
	os.environ['MMGEN_TRACEBACK'] = '1'
	os.environ['PYTHONPATH'] = '.'

	of = 'my.err'
	try: os.unlink(of)
	except: pass

	return of

def traceback_run_process_exception():
	import traceback,re
	l = traceback.format_exception(*sys.exc_info()) # returns a list

	for n in range(len(l)):
		l[n] = re.sub('File "<string>"','File "{}"'.format(traceback_run_execed_file),l[n],count=1)

	exc = l.pop()
	if exc[:11] == 'SystemExit:': l.pop()
	if False: # was: if os.getenv('MMGEN_DISABLE_COLOR'):
		sys.stdout.write('{}{}'.format(''.join(l),exc))
	else:
		def red(s): return '\033[31;1m{}\033[0m'.format(s)
		def yellow(s): return '\033[33;1m{}\033[0m'.format(s)
		sys.stdout.write('{}{}'.format(yellow(''.join(l)),red(exc)))

	open(traceback_run_outfile,'w').write(''.join(l+[exc]))

traceback_run_outfile = traceback_run_init()
traceback_run_tstart = time.time()

try:
	sys.argv.pop(0)
	traceback_run_execed_file = sys.argv[0]
	exec(open(sys.argv[0]).read())
except SystemExit as e:
	if e.code != 0:
		traceback_run_process_exception()
	sys.exit(e.code)
except Exception as e:
	traceback_run_process_exception()
	retval = e.mmcode if hasattr(e,'mmcode') else e.code if hasattr(e,'code') else 1
	sys.exit(retval)

blue = lambda s: s if os.getenv('MMGEN_DISABLE_COLOR') else '\033[34;1m{}\033[0m'.format(s)
sys.stdout.write(blue('Runtime: {:0.5f} secs\n'.format(time.time() - traceback_run_tstart)))
