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
mmgen-regtest: Coin daemon regression test mode setup and operations for the MMGen
               suite
"""

from mmgen.common import *

opts_data = lambda: {
	'desc': 'Coin daemon regression test mode setup and operations for the {} suite'.format(g.proj_name),
	'usage':   '[opts] <command>',
	'sets': ( ('yes', True, 'quiet', True), ),
	'options': """
-h, --help          Print this help message
--, --longhelp      Print help message for long options (common options)
-e, --empty         Don't fund Bob and Alice's wallets on setup
-n, --setup-no-stop-daemon  Don't stop daemon after setup is finished
-q, --quiet         Produce quieter output
-v, --verbose       Produce more verbose output
""",
	'notes': """


                         AVAILABLE COMMANDS

  setup           - set up system for regtest operation with MMGen
  fork COIN       - create a fork of coin COIN
  stop            - stop the regtest coin daemon
  bob             - switch to Bob's wallet, starting daemon if necessary
  alice           - switch to Alice's wallet, starting daemon if necessary
  user            - show current user
  generate N      - mine n blocks (defaults to 1)
  send ADDR AMT   - send amount AMT of miner funds to address ADDR
  test_daemon     - test whether daemon is running
  get_balances    - get balances of Bob and Alice
  show_mempool    - show transaction IDs in mempool
  cli [arguments] - execute an RPC call with arguments
	"""
}

cmd_args = opts.init(opts_data)

cmds = ('setup','stop','generate','test_daemon','create_data_dir','bob','alice','miner','user','send',
		'wait_for_daemon','wait_for_exit','get_current_user','get_balances','show_mempool','cli','fork')

try:
	if cmd_args[0] == 'send':
		assert len(cmd_args) == 3
	elif cmd_args[0] == 'fork':
		assert len(cmd_args) == 2
	elif cmd_args[0] == 'generate':
		assert len(cmd_args) in (1,2)
		if len(cmd_args) == 2:
			cmd_args[1] = int(cmd_args[1])
	elif cmd_args[0] == 'cli':
		pass
	else:
		assert cmd_args[0] in cmds and len(cmd_args) == 1
except:
	opts.usage()
else:
	from mmgen.regtest import *
	globals()[cmd_args[0]](*cmd_args[1:])
