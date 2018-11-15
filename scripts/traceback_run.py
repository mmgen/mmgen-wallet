#!/usr/bin/env python3

# Import as few modules and define as few names as possible at global level before exec'ing the
# file, as all names will be seen by the exec'ed file.  To prevent name collisions, all names
# defined here should begin with 'traceback_run_'

import sys

def traceback_run_init():
	import os
	sys.path.insert(0,'.')

	if 'TMUX' in os.environ: del os.environ['TMUX']
	os.environ['MMGEN_TRACEBACK'] = '1'

	of = os.path.join(os.environ['PWD'],'my.err')
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

	def red(s):    return '{e}[31;1m{}{e}[0m'.format(s,e='\033')
	def yellow(s): return '{e}[33;1m{}{e}[0m'.format(s,e='\033')
	sys.stdout.write('{}{}'.format(yellow(''.join(l)),red(exc)))

	open(traceback_run_outfile,'w').write(''.join(l+[exc]))

traceback_run_outfile = traceback_run_init()

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
	sys.exit(e.mmcode if hasattr(e,'mmcode') else e.code if hasattr(e,'code') else 1)
# else:
# 	print('else: '+repr(sys.exc_info()))
# finally:
# 	print('finally: '+repr(sys.exc_info()))
