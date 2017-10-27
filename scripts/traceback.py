#!/usr/bin/env python
import sys,traceback,os
sys.path.insert(0,'.')

if 'TMUX' in os.environ: del os.environ['TMUX']

f = open('my.err','w')

try:
	sys.argv.pop(0)
	execfile(sys.argv[0])
except SystemExit:
	e = sys.exc_info()
	sys.exit(int(str(e[1])))
except:
	l = traceback.format_exception(*sys.exc_info())
	exc = l.pop()
	def red(s):    return '{e}[31;1m{}{e}[0m'.format(s,e='\033')
	def yellow(s): return '{e}[33;1m{}{e}[0m'.format(s,e='\033')
	sys.stdout.write('{}{}'.format(yellow(''.join(l)),red(exc)))
	traceback.print_exc(file=f)
	sys.exit(1)
