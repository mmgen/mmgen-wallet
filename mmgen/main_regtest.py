#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2017 Philemon <mmgen-py@yandex.com>
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
mmgen-regtest: Bitcoind regression test mode setup and operations for the MMGen
               suite
"""

from mmgen.common import *
opts_data = lambda: {
	'desc': 'Bitcoind regression test mode setup and operations for the {} suite'.format(g.proj_name),
	'usage':   '[opts] <command>',
	'sets': ( ('yes', True, 'quiet', True), ),
	'options': """
-h, --help          Print this help message
-m, --mixed         Create Bob and Alice's wallets with mixed address types
-e, --empty         Don't fund Bob and Alice's wallets on setup
--, --longhelp      Print help message for long options (common options)
-q, --quiet         Produce quieter output
-v, --verbose       Produce more verbose output
""",
	'notes': """


                           AVAILABLE COMMANDS

    setup           - setup up system for regtest operation with MMGen
    stop            - stop the regtest bitcoind
    bob             - switch to Bob's wallet, starting daemon if necessary
    alice           - switch to Alice's wallet, starting daemon if necessary
    user            - show current user
    generate        - mine a block
    test_daemon     - test whether daemon is running
    get_balances    - get balances of Bob and Alice
	"""
}

cmd_args = opts.init(opts_data)

if len(cmd_args) != 1:
	opts.usage()

cmds = ('setup','stop','generate','test_daemon','create_data_dir','bob','alice','user',
		'wait_for_daemon','wait_for_exit','get_current_user','get_balances')

if cmd_args[0] not in cmds:
	opts.usage()

from mmgen.regtest import *

globals()[cmd_args[0]]()
