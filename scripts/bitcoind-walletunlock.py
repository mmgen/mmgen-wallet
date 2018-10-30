#!/usr/bin/env python3
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

import sys,getpass
from mmgen.common import *

opts_data = {
	'prog_name': sys.argv[0].split('/')[-1],
	'desc':    "Unlock a Bitcoin wallet securely",
	'usage':   "[opts]",
	'options': """
-h, --help              Print this help message
-e, --echo-passphrase   Print passphrase to screen when typing it
--, --testnet           Use testnet instead of mainnet
"""
}

cmd_args = opts.init(opts_data)

password = (getpass.getpass,raw_input)[bool(opt.echo_passphrase)]('Enter passphrase: ')

bitcoin_connection().walletpassphrase(password, 9999); msg('OK')
