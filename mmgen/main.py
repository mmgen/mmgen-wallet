#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2014 Philemon <mmgen-py@yandex.com>
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

import sys, termios
from mmgen.util import msg

def main(progname):
	fd = sys.stdin.fileno()
	old = termios.tcgetattr(fd)
	try:
		if   progname == "addrgen":    import mmgen.main_addrgen
		elif progname == "addrimport": import mmgen.main_addrimport
		elif progname == "keygen":     import mmgen.main_addrgen
		elif progname == "passchg":    import mmgen.main_passchg
		elif progname == "pywallet":   import mmgen.main_pywallet
		elif progname == "tool":       import mmgen.main_tool
		elif progname == "txcreate":   import mmgen.main_txcreate
		elif progname == "txsend":     import mmgen.main_txsend
		elif progname == "txsign":     import mmgen.main_txsign
		elif progname == "walletchk":  import mmgen.main_walletchk
		elif progname == "walletgen":  import mmgen.main_walletgen
	except KeyboardInterrupt:
		msg("\nUser interrupt")
		termios.tcsetattr(fd, termios.TCSADRAIN, old)
		sys.exit(1)
