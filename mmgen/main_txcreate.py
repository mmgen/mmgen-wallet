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
mmgen-txcreate: Create a cryptocoin transaction with MMGen- and/or non-MMGen
                inputs and outputs
"""

from .cfg import gc, Config
from .util import fmt_list, async_run

opts_data = {
	'sets': [('yes', True, 'quiet', True)],
	'text': {
		'desc': f'Create a transaction with outputs to specified coin or {gc.proj_name} addresses',
		'usage':   '[opts]  [<addr,amt> ...] <change addr, addrlist ID or addr type> [addr file ...]',
		'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long (global) options
-a, --autosign        Create a transaction for offline autosigning (see
                      ‘mmgen-autosign’). The removable device is mounted and
                      unmounted automatically
-A, --fee-adjust=  f  Adjust transaction fee by factor 'f' (see below)
-B, --no-blank        Don't blank screen before displaying unspent outputs
-c, --comment-file=f  Source the transaction's comment from file 'f'
-C, --fee-estimate-confs=c Desired number of confirmations for fee estimation
                      (default: {cfg.fee_estimate_confs})
-d, --outdir=      d  Specify an alternate directory 'd' for output
-D, --contract-data=D Path to hex-encoded contract data (ETH only)
-E, --fee-estimate-mode=M Specify the network fee estimate mode.  Choices:
                      {fe_all}.  Default: {fe_dfl!r}
-f, --fee=         f  Transaction fee, as a decimal {cu} amount or as
                      {fu} (an integer followed by {fl!r}).
                      See FEE SPECIFICATION below.  If omitted, fee will be
                      calculated using network fee estimation.
-g, --gas=         g  Specify start gas amount in Wei (ETH only)
-i, --info            Display unspent outputs and exit
-I, --inputs=      i  Specify transaction inputs (comma-separated list of
                      MMGen IDs or coin addresses).  Note that ALL unspent
                      outputs associated with each address will be included.
-l, --locktime=    t  Lock time (block height or unix seconds) (default: 0)
-L, --autochg-ignore-labels Ignore labels when autoselecting change addresses
-m, --minconf=     n  Minimum number of confirmations required to spend
                      outputs (default: 1)
-q, --quiet           Suppress warnings; overwrite files without prompting
-R, --no-rbf          Make transaction non-replaceable (non-replace-by-fee
                      according to BIP 125)
-v, --verbose         Produce more verbose output
-V, --vsize-adj=   f  Adjust transaction's estimated vsize by factor 'f'
-y, --yes             Answer 'yes' to prompts, suppress non-essential output
-X, --cached-balances Use cached balances (Ethereum only)
""",
		'notes': '\n{c}\n{F}\n{x}',
	},
	'code': {
		'options': lambda cfg, proto, help_notes, s: s.format(
			fu     = help_notes('rel_fee_desc'),
			fl     = help_notes('fee_spec_letters'),
			fe_all = fmt_list(cfg._autoset_opts['fee_estimate_mode'].choices, fmt='no_spc'),
			fe_dfl = cfg._autoset_opts['fee_estimate_mode'].choices[0],
			cu     = proto.coin,
			cfg    = cfg),
		'notes': lambda cfg, help_notes, s: s.format(
			c      = help_notes('txcreate'),
			F      = help_notes('fee'),
			x      = help_notes('txcreate_examples'))
	}
}

cfg = Config(opts_data=opts_data)

async def main():

	if cfg.autosign:
		from .tx.util import mount_removable_device
		from .autosign import Signable
		asi = mount_removable_device(cfg)
		Signable.automount_transaction(asi).check_create_ok()

	from .tx import NewTX
	tx1 = await NewTX(cfg=cfg, proto=cfg._proto)

	from .rpc import rpc_init
	tx1.rpc = await rpc_init(cfg)

	tx2 = await tx1.create(
		cmd_args = cfg._args,
		locktime = int(cfg.locktime or 0),
		do_info  = cfg.info)

	tx2.file.write(
		outdir                = asi.txauto_dir if cfg.autosign else None,
		ask_write             = not cfg.yes,
		ask_overwrite         = not cfg.yes,
		ask_write_default_yes = False)

async_run(main())
