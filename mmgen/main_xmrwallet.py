#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
mmgen-xmrwallet: Perform various Monero wallet and transacting operations for
                 addresses in an MMGen XMR key-address file
"""
import asyncio

from .cfg import gc, Config
from .util import die, fmt_dict
from . import xmrwallet

opts_data = {
	'sets': [
		('autosign', True, 'watch_only', True),
		('autosign_mountpoint', bool, 'autosign', True),
		('autosign_mountpoint', bool, 'watch_only', True),
	],
	'text': {
		'desc': """Perform various Monero wallet and transacting operations for
                   addresses in an MMGen XMR key-address file""",
		'usage2': [
			'[opts] create | sync | list | view | listview | dump-json | dump | restore [xmr_keyaddrfile] [wallets]',
			'[opts] label    [xmr_keyaddrfile] LABEL_SPEC',
			'[opts] new      [xmr_keyaddrfile] NEW_ADDRESS_SPEC',
			'[opts] transfer [xmr_keyaddrfile] TRANSFER_SPEC',
			'[opts] sweep | sweep_all [xmr_keyaddrfile] SWEEP_SPEC',
			'[opts] submit   [TX_file]',
			'[opts] relay    <TX_file>',
			'[opts] resubmit | abort (for use with --autosign only)',
			'[opts] txview | txlist [TX_file] ...',
			'[opts] export-outputs | export-outputs-sign | import-key-images [wallets]',
		],
		'options': """
-h, --help                       Print this help message
--, --longhelp                   Print help message for long (global) options
-a, --autosign                   Use appropriate outdir and other params for
                                 autosigning operations (implies --watch-only).
                                 When this option is in effect, filename argu-
                                 ments must be omitted, as files are located
                                 automatically.
-c, --compat                     Adjust configuration for compatibility with
                                 the mmgen-tx{{create,sign,send}} family of
                                 commands.  Currently equivalent to
                                 ‘-w {tw_dir}’
-f, --priority=N                 Specify an integer priority ‘N’ for inclusion
                                 of a transaction in the blockchain (higher
                                 number means higher fee).  Valid parameters:
                                 {tp}.  If option
                                 is omitted, the default priority will be used
-F, --full-address               Print addresses in full instead of truncating
-m, --autosign-mountpoint=P      Specify the autosign mountpoint (defaults to
                                 ‘/mnt/mmgen_autosign’, implies --autosign)
-b, --rescan-blockchain          Rescan the blockchain if wallet fails to sync
-d, --outdir=D                   Save transaction files to directory 'D'
                                 instead of the working directory
-D, --daemon=H:P                 Connect to the monerod at {dhp}
-e, --skip-empty-accounts        Skip display of empty accounts in wallets
                                 where applicable
-E, --skip-empty-addresses       Skip display of used empty addresses in
                                 wallets where applicable
-k, --use-internal-keccak-module Force use of the internal keccak module
-p, --hash-preset=P              Use scrypt hash preset 'P' for password
                                 hashing (default: '{gc.dfl_hash_preset}')
-P, --rescan-spent               Perform a rescan of spent outputs.  Used only
                                 with the ‘export-outputs-sign’ operation
-R, --tx-relay-daemon=H:P[:H:P]  Relay transactions via a monerod specified by
                                 {rdhp}
-r, --restore-height=H           Scan from height 'H' when creating wallets.
                                 Use special value ‘current’ to create empty
                                 wallet at current blockchain height.
-R, --no-relay                   Save transaction to file instead of relaying
-s, --no-start-wallet-daemon     Don’t start the wallet daemon at startup
-S, --no-stop-wallet-daemon      Don’t stop the wallet daemon at exit
-W, --watch-only                 Create or operate on watch-only wallets
-w, --wallet-dir=D               Output or operate on wallets in directory 'D'
                                 instead of the working directory
-U, --wallet-rpc-user=user       Wallet RPC username (currently: {cfg.monero_wallet_rpc_user!r})
-P, --wallet-rpc-password=pass   Wallet RPC password (currently: [scrubbed])
""",
	'notes': """

{xmrwallet_help}
"""
	},
	'code': {
		'options': lambda cfg, help_notes, s: s.format(
			dhp = xmrwallet.uarg_info['daemon'].annot,
			rdhp = xmrwallet.uarg_info['tx_relay_daemon'].annot,
			cfg = cfg,
			gc  = gc,
			tw_dir = help_notes('tw_dir'),
			tp  = fmt_dict(xmrwallet.tx_priorities, fmt='equal_compact')
		),
		'notes': lambda help_mod, s: s.format(
			xmrwallet_help = help_mod('xmrwallet')
		)
	}
}

cfg = Config(opts_data=opts_data, init_opts={'coin':'xmr'})

cmd_args = cfg._args

if cmd_args and cfg.autosign and (
		cmd_args[0].replace('-', '_') in (
			xmrwallet.kafile_arg_ops
			+ ('export_outputs', 'export_outputs_sign', 'import_key_images', 'txview', 'txlist')
		)
		or len(cmd_args) == 1 and cmd_args[0] in ('submit', 'resubmit', 'abort')
	):
	cmd_args.insert(1, None)

if len(cmd_args) < 2:
	cfg._usage()

usr_op = cmd_args.pop(0)
op     = usr_op.replace('-', '_')
infile = cmd_args.pop(0)
wallets = spec = None

match op:
	case 'relay' | 'submit' | 'resubmit' | 'abort':
		if len(cmd_args) != 0:
			cfg._usage()
	case 'txview' | 'txlist':
		infile = [infile] + cmd_args
	case 'create' | 'sync' | 'list' | 'view' | 'listview' | 'dump_json' | 'dump' | 'restore':
		if len(cmd_args) > 1:
			cfg._usage()
		wallets = cmd_args.pop(0) if cmd_args else None
	case 'new' | 'transfer' | 'sweep' | 'sweep_all' | 'label':
		if len(cmd_args) != 1:
			cfg._usage()
		spec = cmd_args[0]
	case 'export_outputs' | 'export_outputs_sign' | 'import_key_images':
		if not cfg.autosign:
			die(1, f'--autosign must be used with command {usr_op!r}')
		if len(cmd_args) > 1:
			cfg._usage()
		wallets = cmd_args.pop(0) if cmd_args else None
	case _:
		die(1, f'{usr_op!r}: unrecognized operation')

m = xmrwallet.op(op, cfg, infile, wallets, spec=spec)

if asyncio.run(m.main()):
	m.post_main_success()
else:
	m.post_main_failure()
