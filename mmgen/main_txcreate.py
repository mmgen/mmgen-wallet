#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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
mmgen-txcreate: Create a cryptocoin transaction with MMGen- and/or non-MMGen
                inputs and outputs
"""

from .common import *

opts_data = {
	'sets': [('yes', True, 'quiet', True)],
	'text': {
		'desc': f'Create a transaction with outputs to specified coin or {g.proj_name} addresses',
		'usage':   '[opts]  <addr,amt> ... [change addr] [addr file] ...',
		'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
-a, --tx-fee-adj=  f  Adjust transaction fee by factor 'f' (see below)
-B, --no-blank        Don't blank screen before displaying unspent outputs
-c, --comment-file=f  Source the transaction's comment from file 'f'
-C, --tx-confs=    c  Desired number of confirmations (default: {g.tx_confs})
-d, --outdir=      d  Specify an alternate directory 'd' for output
-D, --contract-data=D Path to hex-encoded contract data (ETH only)
-E, --fee-estimate-mode=M Specify the network fee estimate mode.  Choices:
                      {fe_all}.  Default: {fe_dfl!r}
-f, --tx-fee=      f  Transaction fee, as a decimal {cu} amount or as
                      {fu} (an integer followed by {fl}).
                      See FEE SPECIFICATION below.  If omitted, fee will be
                      calculated using network fee estimation.
-g, --tx-gas=      g  Specify start gas amount in Wei (ETH only)
-i, --info            Display unspent outputs and exit
-I, --inputs=      i  Specify transaction inputs (comma-separated list of
                      MMGen IDs or coin addresses).  Note that ALL unspent
                      outputs associated with each address will be included.
-L, --locktime=    t  Lock time (block height or unix seconds) (default: 0)
-m, --minconf=     n  Minimum number of confirmations required to spend
                      outputs (default: 1)
-q, --quiet           Suppress warnings; overwrite files without prompting
-r, --rbf             Make transaction BIP 125 replaceable (replace-by-fee)
-v, --verbose         Produce more verbose output
-V, --vsize-adj=   f  Adjust transaction's estimated vsize by factor 'f'
-y, --yes             Answer 'yes' to prompts, suppress non-essential output
-X, --cached-balances Use cached balances (Ethereum only)
""",
		'notes': '\n{}{}',
	},
	'code': {
		'options': lambda proto,help_notes,s: s.format(
			fu=help_notes('rel_fee_desc'),
			fl=help_notes('fee_spec_letters'),
			fe_all=fmt_list(g.autoset_opts['fee_estimate_mode'].choices,fmt='no_spc'),
			fe_dfl=g.autoset_opts['fee_estimate_mode'].choices[0],
			cu=proto.coin,
			g=g),
		'notes': lambda help_notes,s: s.format(
			help_notes('txcreate'),
			help_notes('fee'))
	}
}

cmd_args = opts.init(opts_data)

async def main():

	from .protocol import init_proto_from_opts
	proto = init_proto_from_opts()

	from .tx import MMGenTX
	from .tw import TrackingWallet
	tx1 = MMGenTX.New(
		proto = proto,
		tw    = await TrackingWallet(proto) if proto.tokensym else None )

	from .rpc import rpc_init
	tx1.rpc = await rpc_init(proto)

	tx2 = await tx1.create(
		cmd_args = cmd_args,
		locktime = int(opt.locktime or 0),
		do_info  = opt.info )

	tx2.write_to_file(
		ask_write             = not opt.yes,
		ask_overwrite         = not opt.yes,
		ask_write_default_yes = False )

run_session(main())
