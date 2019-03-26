#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>
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
"""

import time

from mmgen.common import *

opts_data = {
	'text': {
		'desc': """
               Split funds in a {pnm} wallet after a chain fork using a
               timelocked transaction
		 """.format(pnm=g.proj_name),
		'usage':'[opts] [output addr1] [output addr2]',
		'options': """
-h, --help           Print this help message
--, --longhelp       Print help message for long options (common options)
-f, --tx-fees=     f The transaction fees for each chain (comma-separated)
-c, --other-coin=  c The coin symbol of the other chain (default: {oc})
-B, --no-blank       Don't blank screen before displaying unspent outputs
-d, --outdir=      d Specify an alternate directory 'd' for output
-m, --minconf=     n Minimum number of confirmations required to spend
                     outputs (default: 1)
-q, --quiet          Suppress warnings; overwrite files without prompting
-r, --rbf            Make transaction BIP 125 replaceable (replace-by-fee)
-v, --verbose        Produce more verbose output
-y, --yes            Answer 'yes' to prompts, suppress non-essential output
-R, --rpc-host2=   h Host the other coin daemon is running on (default: none)
-L, --locktime=    t Lock time (block height or unix seconds)
                     (default: {bh})
""",
	'notes': """\n
This command creates two transactions: one (with the timelock) to be broadcast
on the long chain and one on the short chain after a replayable chain fork.
Only {pnm} addresses may be spent to.

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
""".format(pnm=g.proj_name)
	},
	'code': {
		'options': lambda s: s.format(
			oc=g.proto.forks[-1][2].upper(),
			bh='current block height'),
	}
}

cmd_args = opts.init(opts_data,add_opts=['tx_fee','tx_fee_adj','comment_file'])

opt.other_coin = opt.other_coin.upper() if opt.other_coin else g.proto.forks[-1][2].upper()
if opt.other_coin.lower() not in [e[2] for e in g.proto.forks if e[3] == True]:
	die(1,"'{}': not a replayable fork of {} chain".format(opt.other_coin,g.coin))

if len(cmd_args) != 2:
	fs = 'This command requires exactly two {} addresses as arguments'
	die(1,fs.format(g.proj_name))

from mmgen.obj import MMGenID
try:
	mmids = [MMGenID(a,on_fail='die') for a in cmd_args]
except:
	die(1,'Command line arguments must be valid MMGen IDs')

if mmids[0] == mmids[1]:
	die(2,'Both transactions have the same output! ({})'.format(mmids[0]))

from mmgen.tx import MMGenSplitTX
from mmgen.protocol import init_coin

if opt.tx_fees:
	for idx,g_coin in ((1,opt.other_coin),(0,g.coin)):
		init_coin(g_coin)
		opt.tx_fee = opt.tx_fees.split(',')[idx]
		opts.opt_is_tx_fee(opt.tx_fee,'transaction fee') or sys.exit(1)

rpc_init(reinit=True)

tx1 = MMGenSplitTX()
opt.no_blank = True

gmsg("Creating timelocked transaction for long chain ({})".format(g.coin))
locktime = int(opt.locktime or 0) or g.rpch.getblockcount()
tx1.create(mmids[0],locktime)

tx1.format()
tx1.create_fn()

gmsg("\nCreating transaction for short chain ({})".format(opt.other_coin))

init_coin(opt.other_coin)

tx2 = MMGenSplitTX()
tx2.inputs = tx1.inputs
tx2.inputs.convert_coin()

tx2.create_split(mmids[1])

for tx,desc in ((tx1,'Long chain (timelocked)'),(tx2,'Short chain')):
	tx.desc = desc + ' transaction'
	tx.write_to_file(ask_write=False,ask_overwrite=not opt.yes,ask_write_default_yes=False)
