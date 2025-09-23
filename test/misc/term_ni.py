#!/usr/bin/env python3

import sys, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(sys.argv[0])))))
sys.path[0] = os.curdir

from mmgen.cfg import Config
cfg = Config()

from mmgen.util import msg
from mmgen.term import init_term, get_term
init_term(cfg)
term = get_term()

match sys.argv[1]:
	case 'echo':
		from mmgen.ui import line_input
		from mmgen.term import get_char_raw

		def test_noecho():
			term.init(noecho=True)
			ret = line_input(cfg, 'noecho> ')
			msg(f'==> [{ret.upper()}]')
			get_char_raw()

		def test_echo():
			term.set('echo')
			ret = line_input(cfg, 'echo> ')
			msg(f'==> [{ret.upper()}]')

		test_noecho()
		test_echo()
		test_noecho()

	case 'cleanup':
		term.register_cleanup()
		import tty
		tty.setcbreak(term.stdin_fd)
