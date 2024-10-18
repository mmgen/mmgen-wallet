#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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

from .cfg import gc, Config
from .util import die, async_run

opts_data = {
	'sets': [('yes', True, 'quiet', True)],
	'text': {
		'desc': f'Coin daemon regression test mode setup and operations for the {gc.proj_name} suite',
		'usage':   '[opts] <command>',
		'options': """
-h, --help          Print this help message
--, --longhelp      Print help message for long (global) options
-b, --bdb-wallet    Create and use a legacy Berkeley DB coin daemon wallet
-e, --empty         Don't fund Bob and Alice's wallets on setup
-n, --setup-no-stop-daemon  Don't stop daemon after setup is finished
-q, --quiet         Produce quieter output
-v, --verbose       Produce more verbose output
""",
	'notes': """

                         AVAILABLE COMMANDS

  setup           - set up Bob and Alice regtest mode
  start           - start the regtest coin daemon
  stop            - stop the regtest coin daemon
  generate N      - mine N blocks (defaults to 1)
  send ADDR AMT   - send amount AMT of miner funds to address ADDR
  state           - show current state of daemon (ready, busy, or stopped)
  balances        - get Bob and Alice's balances
  mempool         - show transaction IDs in mempool
  cli             - execute an RPC call with supplied arguments
  wallet_cli      - execute a wallet RPC call with supplied arguments (wallet
                    is first argument)
	"""
	}
}

cfg = Config(opts_data=opts_data)

cmd_args = cfg._args

from .proto.btc.regtest import MMGenRegtest

def check_num_args():
	m = getattr(MMGenRegtest, cmd_args[0])
	margs = m.__code__.co_varnames[1:m.__code__.co_argcount]
	mdfls = m.__defaults__ or ()
	amin = len(margs) - len(mdfls)
	amax = len(margs)
	args = cmd_args[1:]
	m = "{}: too {} arguments for command '%s' (must have no {} than {})" % cmd_args[0]
	if len(args) < amin:
		die(1, m.format(args, 'few', 'less', amin))
	elif len(cmd_args[1:]) > amax:
		die(1, m.format(args, 'many', 'more', amax))

if not cmd_args:
	cfg._usage()
elif cmd_args[0] not in MMGenRegtest.usr_cmds:
	die(1, f'{cmd_args[0]!r}: invalid command')
elif cmd_args[0] not in ('cli', 'wallet_cli', 'balances'):
	check_num_args()

async def main():
	await MMGenRegtest(cfg, cfg.coin, bdb_wallet=cfg.bdb_wallet).cmd(cmd_args)

async_run(main())
