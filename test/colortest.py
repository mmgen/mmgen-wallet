#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>

"""
test/colortest.py: test color handling for the MMGen suite
"""

import os

try:
	from include import test_init
except ImportError:
	from test.include import test_init

from mmgen.color import *
from mmgen.util import msg, ymsg, gmsg
import mmgen.color as color_mod

def test_color():

	ymsg("Terminal display:") # init_color() not called yet, so no yellow here

	for desc, nc in (
			('pre-init', None),
			('auto', 'auto'),
			('8-color', 8),
			('256-color', 256),
			('disabled', 0)):
		if nc is not None:
			init_color(num_colors=nc)
		msg('{:9}: {}'.format(
			desc,
			' '.join(getattr(color_mod, c)(c) for c in sorted(color_mod._colors))))

	init_color()
	gmsg("\nParsed terminfo 'colors' values:")

	from mmgen.color import orange
	for t, c in (
			('rxvt', 8),
			('xterm', 8),
			('rxvt-unicode', 88),
			('screen-256color', 256),
			('xterm-256color', 256)):
		ret = get_terminfo_colors(t)
		if ret is None:
			ymsg(f'Warning: unable to get info for terminal {t!r}')
			continue
		msg(f'{t}: {orange(str(ret))}')
		assert c == ret, f"'colors' value for terminal {t} ({ret}) does not match expected value of {c}"

	ret = get_terminfo_colors()
	msg(f'{os.getenv("TERM")} (this terminal): {orange(str(ret))}')

if __name__ == '__main__':
	test_color()
