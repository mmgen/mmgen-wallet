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
autosign: Auto-sign MMGen transactions, message files and XMR wallet output files
"""

import sys

from .util import msg, die, fmt_list, exit_if_mswin, async_run

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
-l, --seed-len=N      Specify wallet seed length of ‘N’ bits (for setup only)
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
-x, --xmrwallets=L    Range or list of wallets to be used for XMR autosigning
""",
	'notes': """

                               OPERATIONS

clean     - clean the removable device of unneeded files, removing only non-
            essential data
gen_key   - generate the wallet encryption key and copy it to the removable
            device mounted at mountpoint ‘{asi.mountpoint}’ (as currently
            configured)
setup     - full setup: run ‘gen_key’ and create temporary signing wallet(s)
            for all configured coins
xmr_setup - set up Monero temporary signing wallet(s).  Not required during
            normal operation: use ‘setup’ with --xmrwallets instead
macos_ramdisk_setup - set up the ramdisk used for storing the temporary signing
            wallet(s) (macOS only).  Required only when creating the wallet(s)
            manually, without ‘setup’
macos_ramdisk_delete - delete the macOS ramdisk
disable_swap - disable disk swap to prevent potentially sensitive data in
            volatile memory from being swapped to disk.  Applicable only when
            creating temporary signing wallet(s) manually, without ‘setup’
enable_swap - reenable disk swap.  For testing only, should not be invoked in
            a production environment
wait      - start in loop mode: wait-mount-sign-unmount-wait
wipe_key  - wipe the wallet encryption key on the removable device, making
            signing transactions or stealing the user’s seed impossible.
            The operation is intended as a ‘kill switch’ and thus performed
            without prompting


                               USAGE NOTES

If no operation is specified, this program mounts a removable device
(typically a USB flash drive) containing unsigned MMGen transactions, message
files, and/or XMR wallet output files, signs them, unmounts the removable
device and exits.

If invoked with ‘wait’, the program waits in a loop, mounting the removable
device, performing signing operations and unmounting the device every time it
is inserted.

On supported platforms (currently Orange Pi, Rock Pi and Raspberry Pi boards),
the status LED indicates whether the program is busy or in standby mode, i.e.
ready for device insertion or removal.

The removable device must have a partition with a filesystem labeled MMGEN_TX
and a user-writable root directory.  For interoperability between OS-es, it’s
recommended to use the exFAT file system.

On both the signing and online machines the mountpoint ‘{asi.mountpoint}’
(as currently configured) must exist.  Linux (not macOS) machines must have
an ‘/etc/fstab’ with the following entry:

    LABEL=MMGEN_TX {asi.mountpoint} auto noauto,user 0 0

Signing is performed with a temporary wallet created in volatile memory in
the directory ‘{asi.wallet_dir}’ (as currently configured).  The wallet is
encrypted with a 32-byte password saved in the file ‘autosign.key’ in the
root of the removable device’s filesystem.

The password and temporary wallet may be created in one operation by invoking
‘mmgen-autosign setup’ with the removable device inserted.  In this case, the
temporary wallet is created from the user’s default wallet, if it exists and
the user so desires.  If not, the user is prompted to enter a seed phrase.

Alternatively, the password and temporary wallet may be created separately by
first invoking ‘mmgen-autosign gen_key’ and then creating and encrypting the
wallet using the -P (--passwd-file) option:

    $ mmgen-walletconv -iwords -d{asi.wallet_dir} -p1 -N -P{asi.mountpoint}/autosign.key -Lfoo

Note that the hash preset must be ‘1’.  To use a wallet file as the source
instead of an MMGen seed phrase, omit the ‘-i’ option and add the wallet
file path to the end of the command line.  Multiple temporary wallets may
be created in this way and used for signing (note, however, that for XMR
operations only one wallet is supported).

Autosigning is currently supported on Linux and macOS only.


                               SECURITY NOTE

By placing wallet and password on separate devices, this program creates
a two-factor authentication setup whereby an attacker must gain physical
control of both the removable device and signing machine in order to sign
transactions.  It’s therefore recommended to always keep the removable device
secure, separated from the signing machine and hidden (in your pocket, for
example) when not transacting.  In addition, since login access on the
signing machine is required to steal the user’s seed, it’s good practice
to lock the signing machine’s screen once the setup process is complete.

As a last resort, cutting power to the signing machine will destroy the
volatile memory where the temporary wallet resides and foil any attack,
even if you’ve lost control of the removable device.

Always remember to power off the signing machine when your signing session
is over.
"""
	},
	'code': {
		'options': lambda s: s.format(
			asi     = asi,
			mn_fmts = fmt_list(asi.mn_fmts, fmt='no_spc'),
		),
		'notes': lambda s: s.format(asi=asi)
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
