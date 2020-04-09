#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
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

from .common import *

opts_data = {
	'sets': [('yes', True, 'quiet', True)],
	'text': {
		'desc': 'Coin daemon regression test mode setup and operations for the {} suite'.format(g.proj_name),
		'usage':   '[opts] <command>',
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

  setup           - set up Bob and Alice regtest mode
  stop            - stop the regtest coin daemon
  bob             - switch to Bob's wallet, starting daemon if necessary
  alice           - switch to Alice's wallet, starting daemon if necessary
  miner           - switch to Miner's wallet, starting daemon if necessary
  user            - show current user
  generate N      - mine N blocks (defaults to 1)
  send ADDR AMT   - send amount AMT of miner funds to address ADDR
  state           - show current state of daemon (ready, busy, or stopped)
  balances        - get Bob and Alice's balances
  mempool         - show transaction IDs in mempool
  cli             - execute an RPC call with supplied arguments
	"""
	}
}

cmd_args = opts.init(opts_data)

from .regtest import MMGenRegtest

def check_num_args():
	m = getattr(MMGenRegtest,cmd_args[0])
	margs = m.__code__.co_varnames[1:m.__code__.co_argcount]
	mdfls = m.__defaults__ or ()
	amin = len(margs) - len(mdfls)
	amax = len(margs)
	args = cmd_args[1:]
	m = "{}: too {} arguments for command '%s' (must have no {} than {})" % cmd_args[0]
	if len(args) < amin:
		die(1,m.format(args,'few','less',amin))
	elif len(cmd_args[1:]) > amax:
		die(1,m.format(args,'many','more',amax))

if not cmd_args:
	opts.usage()
elif cmd_args[0] not in MMGenRegtest.usr_cmds:
	die(1,'{!r}: invalid command'.format(cmd_args[0]))
elif cmd_args[0] not in ('cli','balances'):
	check_num_args()
MMGenRegtest(g.coin).cmd(cmd_args)
