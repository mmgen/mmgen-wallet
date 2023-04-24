#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
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

from .cfg import Config
from .util import msg,die,fmt_list,exit_if_mswin,async_run

exit_if_mswin('autosigning')

opts_data = {
	'sets': [('stealth_led', True, 'led', True)],
	'text': {
		'desc': 'Auto-sign MMGen transactions, message files and XMR wallet output files',
		'usage':'[opts] [operation]',
		'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
-c, --coins=c         Coins to sign for (comma-separated list)
-I, --no-insert-check Don’t check for device insertion
-l, --led             Use status LED to signal standby, busy and error
-m, --mountpoint=M    Specify an alternate mountpoint 'M'
                      (default: {asi.dfl_mountpoint!r})
-M, --mnemonic-fmt=F  During setup, prompt for mnemonic seed phrase of format
                      'F' (choices: {mn_fmts}; default: {asi.dfl_mn_fmt!r})
-n, --no-summary      Don’t print a transaction summary
-s, --stealth-led     Stealth LED mode - signal busy and error only, and only
                      after successful authorization.
-S, --full-summary    Print a full summary of each signed transaction after
                      each autosign run. The default list of non-MMGen outputs
                      will not be printed.
-q, --quiet           Produce quieter output
-v, --verbose         Produce more verbose output
-w, --wallet-dir=D    Specify an alternate wallet dir
                      (default: {asi.dfl_wallet_dir!r})
-x, --xmrwallets=L    Range or list of wallets to be used for XMR autosigning
""",
	'notes': """

                               OPERATIONS

gen_key - generate the wallet encryption key and copy it to the mountpoint
          {asi.mountpoint!r} (as currently configured)
setup   - generate both wallet encryption key and temporary signing wallet
wait    - start in loop mode: wait-mount-sign-unmount-wait


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

The removable device must have a partition labeled MMGEN_TX with a user-
writable root directory and a directory named ‘/tx’, where unsigned MMGen
transactions are placed.  Optionally, the directory ‘/msg’ may be created
and unsigned message files produced by ‘mmgen-msg’ placed there.

On both the signing and online machines the mountpoint ‘{asi.mountpoint}’
(as currently configured) must exist and ‘/etc/fstab’ must contain the
following entry:

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

Autosigning is currently available only on Linux-based platforms.


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
			mn_fmts = fmt_list( asi.mn_fmts, fmt='no_spc' ),
		),
		'notes': lambda s: s.format(asi=asi)
	}
}

from .autosign import Autosign,AutosignConfig

cfg = AutosignConfig(
	opts_data = opts_data,
	init_opts = {
		'quiet': True,
		'out_fmt': 'wallet',
		'usr_randchars': 0,
		'hash_preset': '1',
		'label': 'Autosign Wallet',
	},
	do_post_init = True )

cmd_args = cfg._args

asi = Autosign(cfg)

cfg._post_init()

if len(cmd_args) not in (0,1):
	cfg._opts.usage()

if len(cmd_args) == 1:
	cmd = cmd_args[0]
	if cmd == 'gen_key':
		asi.gen_key()
		sys.exit(0)
	elif cmd == 'setup':
		asi.setup()
		from .ui import keypress_confirm
		if cfg.xmrwallets and keypress_confirm( cfg, '\nContinue with Monero setup?', default_yes=True ):
			msg('')
			asi.xmr_setup()
		sys.exit(0)
	elif cmd != 'wait':
		die(1,f'{cmd!r}: unrecognized command')

asi.init_led()

asi.init_exit_handler()

async def main():

	await asi.check_daemons_running()

	if not cmd_args:
		ret = await asi.do_sign()
		asi.at_exit(not ret)
	elif cmd_args[0] == 'wait':
		await asi.do_loop()

async_run(main())
