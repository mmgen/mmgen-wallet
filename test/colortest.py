#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>

"""
colortest.py:  test color handling for the MMGen suite
"""

import tests_header
from test.common import *
from mmgen.color import *
from mmgen.color import _colors
init_color()

def test_color():
	try:
		import colorama
		start_mscolor()
	except:
		pass

	gmsg("Parsed terminfo 'colors' values:")

	for t,c in (('rxvt',8),('xterm',8),('rxvt-unicode',88),('screen-256color',256),('xterm-256color',256)):
		ret = get_terminfo_colors(t)
		if ret == None:
			ymsg('Warning: unable to get info for terminal {!r}'.format(t))
			continue
		msg('{}: {}'.format(t,ret))
		assert c == ret, "'colors' value for terminal {} ({}) does not match expected value of {}".format(t,ret,c)

	ret = get_terminfo_colors()
	msg('This terminal ({}): {}'.format(os.getenv('TERM'),ret))

	gmsg("Terminal display:")

	for desc,n in (('auto','auto'),('8-color',8),('256-color',256)):
		init_color(num_colors=n)
		msg('{:9}: {}'.format(desc,' '.join([globals()[c](c) for c in sorted(_colors)])))

test_color()
