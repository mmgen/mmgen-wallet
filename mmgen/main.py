#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
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
main: Script launcher for the MMGen project
"""

def launch(mod,package='mmgen'):

	if mod in ('walletgen','walletchk','walletconv','passchg','subwalletgen','seedsplit'):
		mod = 'wallet'

	if mod == 'keygen':
		mod = 'addrgen'

	import sys,os
	from .globalvars import gc

	if gc.platform == 'linux' and sys.stdin.isatty():
		import termios,atexit
		fd = sys.stdin.fileno()
		old = termios.tcgetattr(fd)
		atexit.register(lambda: termios.tcsetattr(fd,termios.TCSADRAIN,old))

	try:
		__import__(f'{package}.main_{mod}')
	except KeyboardInterrupt:
		sys.stderr.write('\nUser interrupt\n')
		sys.exit(1) # must exit normally so exit handlers will be called
	except EOFError:
		sys.stderr.write('\nEnd of file\n')
	except Exception as e:

		if os.getenv('MMGEN_EXEC_WRAPPER'):
			raise
		else:
			try:
				errmsg = '{}'.format(e.args[0])
			except:
				errmsg = repr(e.args[0])

			from collections import namedtuple
			from mmgen.color import nocolor,yellow,red

			_o = namedtuple('exit_data',['color','exit_val','fs'])
			d = {
				0:   _o(nocolor, 0, '{message}'),
				1:   _o(nocolor, 1, '{message}'),
				2:   _o(yellow,  2, '{message}'),
				3:   _o(yellow,  3, '\nMMGen Error ({name}):\n{message}'),
				4:   _o(red,     4, '\nMMGen Fatal Error ({name}):\n{message}'),
				'x': _o(yellow,  5, '\nMMGen Unhandled Exception ({name}):\n{message}'),
			}[getattr(e,'mmcode','x')]

			(sys.stdout if getattr(e,'stdout',None) else sys.stderr).write(
				d.color(d.fs.format(
					name = type(e).__name__,
					message = errmsg ))
				+ '\n' )

			sys.exit(d.exit_val)

	except SystemExit as e:
		if os.getenv('MMGEN_EXEC_WRAPPER') and e.code != 0:
			from mmgen.color import red
			sys.stdout.write(red(f'{type(e).__name__}: {e}\n'))
		raise
