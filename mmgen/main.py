#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2015 Philemon <mmgen-py@yandex.com>
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

	import os
	t = "MMGEN_USE_OLD_SCRIPTS"
	if not (t in os.environ and os.environ[t]):
		if what in ("walletgen","walletchk","passchg"):
			what = "wallet"

	if what == "walletconv": what = "wallet"
	if what == "keygen":     what = "addrgen"

	try: import termios
	except: __import__("mmgen.main_" + what) # Windows
	else:
		import sys,atexit
		fd = sys.stdin.fileno()
		old = termios.tcgetattr(fd)
		def at_exit():
			termios.tcsetattr(fd, termios.TCSADRAIN, old)
		atexit.register(at_exit)
		try: __import__("mmgen.main_" + what)
		except KeyboardInterrupt:
			sys.stderr.write("\nUser interrupt\n")
		except EOFError:
			sys.stderr.write("\nEnd of file\n")
