#!/usr/bin/env python
import sys,traceback,os
sys.path.insert(0,'.')

if 'TMUX' in os.environ: del os.environ['TMUX']
os.environ['MMGEN_TRACEBACK'] = '1'

tb_source = open(sys.argv[1])
tb_file = open('my.err','w')

try:
	sys.argv.pop(0)
	exec tb_source
except SystemExit:
#	pass
	e = sys.exc_info()
	sys.exit(int(str(e[1])))
except:
	l = traceback.format_exception(*sys.exc_info())
	exc = l.pop()
	def red(s):    return '{e}[31;1m{}{e}[0m'.format(s,e='\033')
	def yellow(s): return '{e}[33;1m{}{e}[0m'.format(s,e='\033')
	sys.stdout.write('{}{}'.format(yellow(''.join(l)),red(exc)))
	traceback.print_exc(file=tb_file)
	sys.exit(1)
