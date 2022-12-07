#!/usr/bin/env python3

import sys,os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(sys.argv[0])))))
sys.path[0] = os.curdir

from mmgen.common import *

cmd_args = opts.init()

from mmgen.term import get_term,get_char_raw
term = get_term()

if cmd_args[0] == 'echo':

	from mmgen.ui import line_input

	term.init(noecho=True)
	line_input('noecho> ')
	get_char_raw()

	term.set('echo')
	line_input('echo> ')

	term.set('noecho')
	line_input('noecho> ')
	get_char_raw()

elif cmd_args[0] == 'cleanup':

	term.register_cleanup()

	import tty
	tty.setcbreak(term.stdin_fd)
