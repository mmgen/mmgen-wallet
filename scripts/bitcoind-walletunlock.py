#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C) 2013 by philemon <mmgen-py@yandex.com>
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
bitcoind-walletunlock.py: Unlock a Bitcoin wallet securely
"""

import sys
from mmgen.Opts import *
from mmgen.tx import *
from mmgen.utils import msg, my_getpass, my_raw_input

prog_name = sys.argv[0].split("/")[-1]

help_data = {
	'prog_name': prog_name,
	'desc':    "Unlock a Bitcoin wallet securely",
	'usage':   "[opts]",
	'options': """
-h, --help                 Print this help message
-e, --echo-passphrase      Print passphrase to screen when typing it
"""
}

short_opts = "he"
long_opts  = "help","echo_passphrase"

opts,cmd_args = process_opts(sys.argv,help_data,short_opts,long_opts)

c = connect_to_bitcoind()

prompt = "Enter passphrase: "
if 'echo_passphrase' in opts:
	password = my_raw_input(prompt)
else:
	password = my_getpass(prompt)

from bitcoinrpc import exceptions

try:
	c.walletpassphrase(password, 9999)
except exceptions.WalletWrongEncState:
	msg("Wallet is unencrypted")
except exceptions.WalletPassphraseIncorrect:
	msg("Passphrase incorrect")
except exceptions.WalletAlreadyUnlocked:
	msg("WARNING: Wallet already unlocked!")
