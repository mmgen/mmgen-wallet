#!/usr/bin/env python3

import sys,os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(sys.argv[0])))))
sys.path[0] = os.curdir

from mmgen.cfg import Config
cfg = Config()

from mmgen.term import init_term,get_term
init_term(cfg)
term = get_term()

if sys.argv[1] == 'echo':

	from mmgen.ui import line_input
	from mmgen.term import get_char_raw

	term.init(noecho=True)
	line_input( cfg, 'noecho> ' )
	get_char_raw()

	term.set('echo')
	line_input( cfg, 'echo> ' )

	term.set('noecho')
	line_input( cfg, 'noecho> ' )
	get_char_raw()

elif sys.argv[1] == 'cleanup':

	term.register_cleanup()

	import tty
	tty.setcbreak(term.stdin_fd)
