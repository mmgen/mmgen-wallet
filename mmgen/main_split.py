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

# TODO: check that balances of output addrs are zero?

"""
mmgen-split: Split funds after a replayable chain fork using a timelocked transaction
             UNMAINTAINED
"""

from .cfg import Config, gc
from .util import gmsg, die

opts_data = {
	'text': {
		'desc': f"""
               Split funds in an {gc.proj_name} wallet after a chain fork using a
               timelocked transaction
		 """,
		'usage':'[opts] [output addr1] [output addr2]',
		'options': """
-h, --help           Print this help message
--, --longhelp       Print help message for long (global) options
-f, --tx-fees=     f The transaction fees for each chain (comma-separated)
-c, --other-coin=  c The coin symbol of the other chain (default: {oc})
-B, --no-blank       Don't blank screen before displaying unspent outputs
-d, --outdir=      d Specify an alternate directory 'd' for output
-m, --minconf=     n Minimum number of confirmations required to spend
                     outputs (default: 1)
-q, --quiet          Suppress warnings; overwrite files without prompting
-R, --no-rbf         Make transaction non-replaceable (non-replace-by-fee
                     according to BIP 125)
-v, --verbose        Produce more verbose output
-y, --yes            Answer 'yes' to prompts, suppress non-essential output
-R, --rpc-host2=   h Host the other coin daemon is running on (default: none)
-l, --locktime=    t Lock time (block height or unix seconds)
                     (default: {bh})
""",
	'notes': f"""\n
This command creates two transactions: one (with the timelock) to be broadcast
on the long chain and one on the short chain after a replayable chain fork.
Only {gc.proj_name} addresses may be spent to.

The command must be run on the longest chain.  The user is reponsible for
ensuring that the current chain is the longest.  The other chain is specified
on the command line, or it defaults to the most recent replayable fork of the
current chain.

For the split to have a reasonable chance of succeeding, the long chain should
be well ahead of the short one (by more than 20 blocks or so) and transactions
should have a good chance of confirming quickly on both chains.  For this
larger than normal fees may be required.  Fees may be specified on the command
line, or network fee estimation may be used.

If the split fails (i.e. the long-chain TX is broadcast and confirmed on the
short chain), no funds are lost.  A new split attempt can be made with the
long-chain transaction's output as an input for the new split transaction.
This process can be repeated as necessary until the split succeeds.

IMPORTANT: Timelock replay protection offers NO PROTECTION against reorg
attacks on the majority chain or reorg attacks on the minority chain if the
minority chain is ahead of the timelock.  If the reorg'd minority chain is
behind the timelock, protection is contingent on getting the non-timelocked
transaction reconfirmed before the timelock expires. Use at your own risk.
"""
	},
	'code': {
		'options': lambda proto, s: s.format(
			oc = proto.forks[-1][2].upper(),
			bh = 'current block height'),
	}
}

cfg = Config(opts_data=opts_data, need_amt=False)

proto = cfg._proto

die(1, 'This command is disabled')

# the following code is broken:
cfg.other_coin = cfg.other_coin.upper() if cfg.other_coin else proto.forks[-1][2].upper()
if cfg.other_coin.lower() not in [e[2] for e in proto.forks if e[3] is True]:
	die(1, f'{cfg.other_coin!r}: not a replayable fork of {proto.coin} chain')

if len(cfg._args) != 2:
	die(1, f'This command requires exactly two {gc.proj_name} addresses as arguments')

from .addr import MMGenID
try:
	mmids = [MMGenID(proto, a) for a in cfg._args]
except:
	die(1, 'Command line arguments must be valid MMGen IDs')

if mmids[0] == mmids[1]:
	die(2, f'Both transactions have the same output! ({mmids[0]})')

from .tx import MMGenSplitTX
from .protocol import init_proto

if cfg.tx_fees:
	for idx, g_coin in ((1, cfg.other_coin), (0, proto.coin)):
		proto = init_proto(cfg, g_coin)
		cfg.fee = cfg.tx_fees.split(',')[idx]
#		opts.opt_is_tx_fee('foo', cfg.fee, 'transaction fee') # raises exception on error

tx1 = MMGenSplitTX(proto)
cfg.no_blank = True

async def main():
	gmsg(f'Creating timelocked transaction for long chain ({proto.coin})')
	locktime = int(cfg.locktime)
	if not locktime:
		from .rpc import rpc_init
		rpc = rpc_init(proto)
		locktime = rpc.call('getblockcount')
	tx1.create(mmids[0], locktime)

	tx1.format()
	tx1.create_fn()

	gmsg(f'\nCreating transaction for short chain ({cfg.other_coin})')

	proto2 = init_proto(cfg, cfg.other_coin)

	tx2 = MMGenSplitTX(proto2)
	tx2.inputs = tx1.inputs
	tx2.inputs.convert_coin()

	tx2.create_split(mmids[1])

	for tx, desc in ((tx1, 'Long chain (timelocked)'), (tx2, 'Short chain')):
		tx.desc = desc + ' transaction'
		tx.file.write(ask_write=False, ask_overwrite=not cfg.yes, ask_write_default_yes=False)
