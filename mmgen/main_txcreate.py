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

target = gc.prog_name.split('-')[1].removesuffix('create')

opts_data = {
	'filter_codes': {
		'tx':     ['-', 't'],
		'swaptx': ['-', 's'],
	}[target],
	'sets': [('yes', True, 'quiet', True)],
	'text': {
		'desc': {
			'tx':     f'Create a transaction with outputs to specified coin or {gc.proj_name} addresses',
			'swaptx': f'Create a DEX swap transaction with {gc.proj_name} inputs and outputs',
		}[target],
		'usage':   '[opts] {u_args} [addr file ...]',
		'options': """
			-- -h, --help            Print this help message
			-- --, --longhelp        Print help message for long (global) options
			-- -a, --autosign        Create a transaction for offline autosigning (see
			+                        ‘mmgen-autosign’). The removable device is mounted and
			+                        unmounted automatically
			-- -A, --fee-adjust=  f  Adjust transaction fee by factor 'f' (see below)
			-- -B, --no-blank        Don't blank screen before displaying {a_info}
			-- -c, --comment-file=f  Source the transaction's comment from file 'f'
			b- -C, --fee-estimate-confs=c Desired number of confirmations for fee estimation
			+                        (default: {cfg.fee_estimate_confs})
			-- -d, --outdir=      d  Specify an alternate directory 'd' for output
			e- -D, --contract-data=D Path to file containing hex-encoded contract data
			b- -E, --fee-estimate-mode=M Specify the network fee estimate mode.  Choices:
			+                        {fe_all}.  Default: {fe_dfl!r}
			-- -f, --fee=         f  Transaction fee, as a decimal {cu} amount or as
			+                        {fu} (an integer followed by {fl!r}).
			+                        See FEE SPECIFICATION below.  If omitted, fee will be
			+                        calculated using network fee estimation.
			e- -g, --gas=         g  Specify start gas amount in Wei
			-- -i, --info            Display {a_info} and exit
			-- -I, --inputs=      i  Specify transaction inputs (comma-separated list of
			+                        MMGen IDs or coin addresses).  Note that ALL unspent
			+                        outputs associated with each address will be included.
			bt -l, --locktime=    t  Lock time (block height or unix seconds) (default: 0)
			b- -L, --autochg-ignore-labels Ignore labels when autoselecting change addresses
			-- -m, --minconf=     n  Minimum number of confirmations required to spend
			+                        outputs (default: 1)
			-- -q, --quiet           Suppress warnings; overwrite files without prompting
			bt -R, --no-rbf          Make transaction non-replaceable (non-replace-by-fee
			+                        according to BIP 125)
			-- -v, --verbose         Produce more verbose output
			b- -V, --vsize-adj=   f  Adjust transaction's estimated vsize by factor 'f'
			-s -x, --swap-proto      Swap protocol to use (Default: {x_dfl},
			+                        Choices: {x_all})
			-- -y, --yes             Answer 'yes' to prompts, suppress non-essential output
			e- -X, --cached-balances Use cached balances
		""",
		'notes': '\n{c}\n{n_at}\n\n{F}\n{x}',
	},
	'code': {
		'usage': lambda cfg, proto, help_notes, s: s.format(
			u_args = help_notes('txcreate_args', target)),
		'options': lambda cfg, proto, help_notes, s: s.format(
			cfg    = cfg,
			cu     = proto.coin,
			a_info = help_notes('account_info_desc'),
			fu     = help_notes('rel_fee_desc'),
			fl     = help_notes('fee_spec_letters'),
			fe_all = fmt_list(cfg._autoset_opts['fee_estimate_mode'].choices, fmt='no_spc'),
			fe_dfl = cfg._autoset_opts['fee_estimate_mode'].choices[0],
			x_all = fmt_list(cfg._autoset_opts['swap_proto'].choices, fmt='no_spc'),
			x_dfl = cfg._autoset_opts['swap_proto'].choices[0]),
		'notes': lambda cfg, help_notes, s: s.format(
			c      = help_notes('txcreate'),
			F      = help_notes('fee'),
			x      = help_notes('txcreate_examples'),
			n_at   = help_notes('address_types'))
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
	tx1 = await NewTX(cfg=cfg, proto=cfg._proto, target=target)

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
