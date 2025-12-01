#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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
from .util import Msg, fmt_list, fmt_dict, async_run
from .xmrwallet import tx_priorities

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
			'swaptx': f'Create a DEX swap transaction from one {gc.proj_name} tracking wallet to another',
		}[target],
		'usage':   '[opts] {u_args}',
		'options': """
			-- -h, --help            Print this help message
			-- --, --longhelp        Print help message for long (global) options
			-- -a, --autosign        Create a transaction for offline autosigning (see
			+                        ‘mmgen-autosign’). The removable device is mounted and
			+                        unmounted automatically
			R- -A, --fee-adjust=  f  Adjust transaction fee by factor ‘f’ (see below)
			-- -B, --no-blank        Don't blank screen before displaying {a_info}
			-- -c, --comment-file=f  Source the transaction's comment from file 'f'
			b- -C, --fee-estimate-confs=c Desired number of confirmations for fee estimation
			+                        (default: {cfg.fee_estimate_confs})
			-- -d, --outdir=      d  Specify an alternate directory 'd' for output
			e- -D, --contract-data=D Path to file containing hex-encoded contract data
			b- -E, --fee-estimate-mode=M Specify the network fee estimate mode.  Choices:
			+                        {fe_all}.  Default: {fe_dfl!r}
			R- -f, --fee=         f  Transaction fee, as a decimal {cu} amount or as
			+                        {fu} (an integer followed by {fl}).
			+                        See FEE SPECIFICATION below.  If omitted, fee will be
			+                        calculated using network fee estimation.
			et -g, --gas=N           Set the gas limit (see GAS LIMIT below)
			-s -g, --gas=N           Set the gas limit for Ethereum (see GAS LIMIT below)
			-s -G, --router-gas=N    Set the gas limit for the Ethereum router contract
			+                        (integer).  When unset, a hardcoded default will be
			+                        used.  Applicable only for swaps from token assets.
			-- -i, --info            Display {a_info} and exit
			R- -I, --inputs=      i  Specify transaction inputs (comma-separated list of
			+                        MMGen IDs or coin addresses).  Note that ALL unspent
			+                        outputs associated with each address will be included.
			bt -l, --locktime=    t  Lock time (block height or unix seconds) (default: 0)
			-s -l, --trade-limit=L   Minimum swap amount, as either percentage or absolute
			+                        coin amount (see TRADE LIMIT below)
			b- -L, --autochg-ignore-labels Ignore labels when autoselecting change addresses
			-- -m, --minconf=     n  Minimum number of confirmations required to spend
			+                        outputs (default: 1)
			m- -p, --priority=N      Specify an integer priority ‘N’ for inclusion of trans-
			+                        action in blockchain (higher number means higher fee).
			+                        Valid parameters: {tp}.
			+                        If option is omitted, the default priority will be used
			-- -q, --quiet           Suppress warnings; overwrite files without prompting
			-s -r, --stream-interval=N Set block interval for streaming swap (default: {si})
			bt -R, --no-rbf          Make transaction non-replaceable (non-replace-by-fee
			+                        according to BIP 125)
			-s -s, --swap-proto      Swap protocol to use (Default: {x_dfl},
			+                        Choices: {x_all})
			-s -S, --list-assets     List available swap assets
			-- -v, --verbose         Produce more verbose output
			b- -V, --vsize-adj=   f  Adjust transaction's estimated vsize by factor 'f'
			rs -x, --proxy=P         Fetch the swap quote via SOCKS5h proxy ‘P’ (host:port).
			+                        Use special value ‘env’ to honor *_PROXY environment
			+                        vars instead.
			X- -x, --proxy=P         Connect to remote server(s) via SOCKS5h proxy ‘P’
			+                        (host:port).  Use special value ‘env’ to honor *_PROXY
			+                        environment vars instead.
			-- -y, --yes             Answer 'yes' to prompts, suppress non-essential output
			e- -X, --cached-balances Use cached balances
		""",
		'notes': '\n{c}\n{n_at}\n\n{g}{F}{x}',
	},
	'code': {
		'usage': lambda cfg, proto, help_notes, s: s.format(
			u_args = help_notes(f'{target}create_args')),
		'options': lambda cfg, proto, help_notes, s: s.format(
			cfg    = cfg,
			cu     = proto.coin,
			a_info = help_notes('account_info_desc'),
			fu     = help_notes('rel_fee_desc'),
			fl     = help_notes('fee_spec_letters', use_quotes=True),
			tp     = fmt_dict(tx_priorities, fmt='equal_compact'),
			si     = help_notes('stream_interval'),
			fe_all = fmt_list(cfg._autoset_opts['fee_estimate_mode'].choices, fmt='no_spc'),
			fe_dfl = cfg._autoset_opts['fee_estimate_mode'].choices[0],
			x_all = fmt_list(cfg._autoset_opts['swap_proto'].choices, fmt='no_spc'),
			x_dfl = cfg._autoset_opts['swap_proto'].choices[0]),
		'notes': lambda cfg, help_mod, help_notes, s: s.format(
			c      = help_mod(f'{target}create'),
			g      = help_notes('gas_limit', target),
			F      = help_notes('fee', all_coins={'tx': False, 'swaptx': True}[target]),
			n_at   = help_notes('address_types'),
			x      = help_mod(f'{target}create_examples'))
	}
}

cfg = Config(opts_data=opts_data)

if cfg.list_assets:
	import sys
	from .tx.new_swap import get_swap_proto_mod
	sp = get_swap_proto_mod(cfg.swap_proto)
	Msg('AVAILABLE SWAP ASSETS:\n' + sp.SwapAsset('BTC', 'send').fmt_assets_data(indent='  '))
	sys.exit(0)

if not (cfg.info or cfg.contract_data) and len(cfg._args) < {'tx': 1, 'swaptx': 2}[target]:
	cfg._usage()

async def main():

	if cfg.autosign:
		from .tx.util import mount_removable_device
		from .autosign import Signable
		asi = mount_removable_device(cfg, add_cfg={'xmrwallet_compat': True})
		Signable.automount_transaction(asi).check_create_ok()

	if target == 'swaptx':
		from .tx.new_swap import get_send_proto
		proto = get_send_proto(cfg)
	else:
		proto = cfg._proto

	from .tx import NewTX
	tx1 = NewTX(cfg=cfg, proto=proto, target=target)

	tx2 = await tx1.create(
		cmd_args = cfg._args,
		locktime = int(cfg.locktime or 0),
		do_info  = cfg.info)

	if not tx1.is_compat:
		tx2.file.write(
			outdir                = asi.txauto_dir if cfg.autosign else None,
			ask_write             = not cfg.yes,
			ask_overwrite         = not cfg.yes,
			ask_write_default_yes = False)

async_run(cfg, main)
