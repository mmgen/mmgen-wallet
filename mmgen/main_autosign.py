#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
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
autosign: Auto-sign MMGen transactions, message files and XMR wallet output files
"""

import sys

from .util import msg, ymsg, gmsg, die, fmt_list, exit_if_mswin, async_run

exit_if_mswin('autosigning')

opts_data = {
	'sets': [('stealth_led', True, 'led', True)],
	'text': {
		'desc': 'Auto-sign MMGen transactions, message files and XMR wallet output files',
		'usage':'[opts] [operation]',
		'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long (global) options
-c, --coins=c         Coins to sign for (comma-separated list)
-I, --no-insert-check Don’t check for device insertion
-k, --keys-from-file=F Use wif keys listed in file ‘F’ for signing non-MMGen
                      inputs. The file may be MMGen encrypted if desired. The
                      ‘setup’ operation creates a temporary encrypted copy of
                      the file in volatile memory for use during the signing
                      session, thus permitting the deletion of the original
                      file for increased security.
-l, --seed-len=N      Specify wallet seed length of ‘N’ bits (for setup with
                      mnemonic seed phrase only)
-L, --led             Use status LED to signal standby, busy and error
-m, --mountpoint=M    Specify an alternate mountpoint 'M'
                      (default: {asi.dfl_mountpoint!r})
-M, --mnemonic-fmt=F  During setup, prompt for mnemonic seed phrase of format
                      'F' (choices: {mn_fmts}; default: {asi.dfl_mn_fmt!r})
-n, --no-summary      Don’t print a transaction summary
-r, --macos-ramdisk-size=S  Set the size (in MB) of the ramdisk used to store
                      the offline signing wallet(s) on macOS machines.  By
                      default, a runtime-calculated value will be used. This
                      option is of interest only for setups with unusually
                      large Monero wallets
-s, --stealth-led     Stealth LED mode - signal busy and error only, and only
                      after successful authorization.
-S, --full-summary    Print a full summary of each signed transaction after
                      each autosign run. The default list of non-MMGen outputs
                      will not be printed.
-q, --quiet           Produce quieter output
-v, --verbose         Produce more verbose output
-w, --wallet-dir=D    Specify an alternate wallet dir
                      (default: {asi.dfl_wallet_dir!r})
-W, --allow-non-wallet-swap Allow signing of swap transactions that send funds
                      to non-wallet addresses
-x, --xmrwallets=L    Range or list of wallet numbers to be used for XMR
                      autosigning
""",
	'notes': '{n_as}'
	},
	'code': {
		'options': lambda s: s.format(
			asi     = asi,
			mn_fmts = fmt_list(asi.mn_fmts, fmt='no_spc'),
		),
		'notes': lambda s, help_mod: s.format(
			n_as = help_mod('autosign', asi=asi))
	}
}

def main(do_loop):

	asi.init_led()
	asi.init_exit_handler()

	async def do():
		await asi.check_daemons_running()
		if do_loop:
			await asi.main_loop()
		else:
			ret = await asi.do_sign()
			asi.at_exit(not ret)

	async_run(cfg, do)

from .cfg import Config
from .autosign import Autosign

cfg = Config(
	opts_data = opts_data,
	init_opts = {
		'out_fmt': 'wallet',
		'usr_randchars': 0,
		'hash_preset': '1',
		'label': 'Autosign Wallet'},
	caller_post_init = True)

cmd = cfg._args[0] if len(cfg._args) == 1 else 'sign' if not cfg._args else cfg._usage()

if cmd not in Autosign.cmds + Autosign.util_cmds:
	die(1, f'‘{cmd}’: unrecognized command')

if cmd in ('test_led', 'list_led'):
	from .led import LEDControl
	match cmd:
		case 'list_led':
			msg(
				'Boards with tested LED signaling support:\n' +
				'\n'.join(f'  {v.name}' for k, v in LEDControl.boards.items() if k != 'dummy'))
		case 'test_led':
			from .exception import NoLEDSupport
			try:
				LEDControl(enabled=True)
			except NoLEDSupport:
				ymsg('No LED signaling support for this platform')
			else:
				gmsg('LED signaling is supported by this platform!')
	sys.exit(0)

if cmd != 'setup':
	for opt in ('seed_len', 'mnemonic_fmt', 'keys_from_file'):
		if getattr(cfg, opt):
			die(1, f'--{opt.replace("_", "-")} is valid only for the ‘setup’ operation')

if cmd not in ('sign', 'wait'):
	for opt in ('no_summary', 'led', 'stealth_led', 'full_summary'):
		if getattr(cfg, opt):
			die(1, f'--{opt.replace("_", "-")} is not valid for the ‘{cmd}’ operation')

asi = Autosign(cfg, cmd=cmd)

cfg._post_init()

match cmd:
	case 'gen_key':
		asi.gen_key()
	case 'setup':
		asi.setup()
		from .ui import keypress_confirm
		if cfg.xmrwallets and keypress_confirm(cfg, '\nContinue with Monero setup?', default_yes=True):
			msg('')
			asi.xmr_setup()
		asi.do_umount()
	case 'xmr_setup':
		if not cfg.xmrwallets:
			die(1, 'Please specify a wallet or range of wallets with the --xmrwallets option')
		asi.do_mount()
		asi.xmr_setup()
		asi.do_umount()
	case 'macos_ramdisk_setup' | 'macos_ramdisk_delete':
		if sys.platform != 'darwin':
			die(1, f'The ‘{cmd}’ operation is for the macOS platform only')
		getattr(asi, cmd)()
	case 'enable_swap':
		asi.swap.enable()
	case 'disable_swap':
		asi.swap.disable()
	case 'sign':
		main(do_loop=False)
	case 'wait':
		main(do_loop=True)
	case 'clean':
		asi.do_mount()
		asi.clean_old_files()
		asi.do_umount()
	case 'wipe_key':
		asi.do_mount()
		asi.wipe_encryption_key()
		asi.do_umount()
