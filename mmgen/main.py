#!/usr/bin/env python
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

	def my_dec(a):
		try:
			return a.decode('utf8')
		except:
			sys.stderr.write("Argument {!r} is not a valid UTF-8 string".format(a))
			sys.exit(2)

	import sys
	sys.argv = map(my_dec,sys.argv)

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
				try: m = u'{}'.format(e.message)
				except:
					try: m = e.message.decode('utf8')
					except: m = repr(e.message)
				from mmgen.util import ydie
				ydie(2,u'\nERROR: ' + m)
