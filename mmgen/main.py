#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
main: Script launcher for the MMGen Project
"""

import sys, os

def launch(*, mod=None, func=None, fqmod=None, package='mmgen'):

	if sys.platform in ('linux', 'darwin') and sys.stdin.isatty():
		import termios, atexit
		fd = sys.stdin.fileno()
		old = termios.tcgetattr(fd)
		atexit.register(lambda: termios.tcsetattr(fd, termios.TCSADRAIN, old))

	try:
		__import__(f'{package}.main_{mod}') if mod else func() if func else __import__(fqmod)
	except KeyboardInterrupt:
		from .color import yellow
		sys.stderr.write(yellow('\nUser interrupt\n'))
		sys.exit(1)
	except EOFError:
		from .color import yellow
		sys.stderr.write(yellow('\nEnd of file\n'))
		sys.exit(1)
	except Exception as e:
		try:
			errmsg = str(e.args[0])
		except:
			errmsg = repr(e.args[0]) if e.args else repr(e)

		from collections import namedtuple
		from .color import nocolor, yellow, red

		_o = namedtuple('exit_data', ['color', 'exit_val', 'fs'])
		d = {
			0:   _o(nocolor, 0, '{message}'),
			1:   _o(nocolor, 1, '{message}'),
			2:   _o(yellow,  2, '{message}'),
			3:   _o(yellow,  3, '\nMMGen Error ({name}):\n{message}'),
			4:   _o(red,     4, '\nMMGen Fatal Error ({name}):\n{message}'),
			'x': _o(yellow,  5, '\nMMGen Python Exception ({name}): {e}'),
		}[getattr(e, 'mmcode', 'x')]

		(sys.stdout if getattr(e, 'stdout', None) else sys.stderr).write(
			d.color(d.fs.format(
				name = type(e).__name__,
				message = errmsg.strip() or e,
				e = e))
			+ '\n')

		if os.getenv('MMGEN_EXEC_WRAPPER') or os.getenv('MMGEN_TRACEBACK'):
			raise

		sys.exit(d.exit_val)
