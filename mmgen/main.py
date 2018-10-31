#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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
main.py - Script launcher for the MMGen suite
"""

def launch(what):

	if what in ('walletgen','walletchk','walletconv','passchg'):
		what = 'wallet'
	if what == 'keygen': what = 'addrgen'

	try: import termios
	except: # Windows
		__import__('mmgen.main_' + what)
	else:
		import os,atexit
		if sys.stdin.isatty():
			fd = sys.stdin.fileno()
			old = termios.tcgetattr(fd)
			def at_exit(): termios.tcsetattr(fd, termios.TCSADRAIN, old)
			atexit.register(at_exit)
		try: __import__('mmgen.main_' + what)
		except KeyboardInterrupt:
			sys.stderr.write('\nUser interrupt\n')
		except EOFError:
			sys.stderr.write('\nEnd of file\n')
		except Exception as e:
			if os.getenv('MMGEN_TRACEBACK'):
				raise
			else:
				try: m = '{}'.format(e.args[0])
				except: m = repr(e.args[0])

				from mmgen.util import die,ydie,rdie
				d = [   (ydie,2,'\nMMGen Unhandled Exception ({n}): {m}'),
						(die, 1,'{m}'),
						(ydie,2,'{m}'),
						(ydie,3,'\nMMGen Error ({n}): {m}'),
						(rdie,4,'\nMMGen Fatal Error ({n}): {m}')
					][e.mmcode if hasattr(e,'mmcode') else 0]

				d[0](d[1],d[2].format(n=type(e).__name__,m=m))
