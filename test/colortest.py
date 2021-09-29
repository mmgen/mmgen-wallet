#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2021 The MMGen Project <mmgen@tuta.io>

"""
colortest.py:  test color handling for the MMGen suite
"""

import include.tests_header
from include.common import *
from mmgen.color import *
from mmgen.color import _colors

def test_color():

	init_color()
	gmsg("Parsed terminfo 'colors' values:")

	for t,c in (('rxvt',8),('xterm',8),('rxvt-unicode',88),('screen-256color',256),('xterm-256color',256)):
		ret = get_terminfo_colors(t)
		if ret == None:
			set_vt100()
			ymsg(f'Warning: unable to get info for terminal {t!r}')
			continue
		msg(f'{t}: {ret}')
		assert c == ret, f"'colors' value for terminal {t} ({ret}) does not match expected value of {c}"

	ret = get_terminfo_colors()
	msg(f'This terminal ({os.getenv("TERM")}): {ret}')
	set_vt100()
	gmsg("Terminal display:")

	for desc,n in (('auto','auto'),('8-color',8),('256-color',256)):
		init_color(num_colors=n)
		msg('{:9}: {}'.format(
			desc,
			' '.join(globals()[c](c) for c in sorted(_colors)) ))

test_color()
