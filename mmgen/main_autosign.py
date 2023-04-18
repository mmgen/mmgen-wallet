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
mmgen-autosign: Auto-sign MMGen transactions and message files
"""

import sys

from .cfg import Config
from .util import die,fmt_list,exit_if_mswin,async_run

exit_if_mswin('autosigning')

opts_data = {
	'sets': [('stealth_led', True, 'led', True)],
	'text': {
		'desc': 'Auto-sign MMGen transactions and message files',
		'usage':'[opts] [command]',
		'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
-c, --coins=c         Coins to sign for (comma-separated list)
-I, --no-insert-check Don’t check for device insertion
-l, --led             Use status LED to signal standby, busy and error
-m, --mountpoint=M    Specify an alternate mountpoint 'M' (default: {asi.dfl_mountpoint!r})
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
""",
	'notes': """

                              COMMANDS

gen_key - generate the wallet encryption key and copy it to the mountpoint
          (currently configured as {asi.mountpoint!r})
setup   - generate the wallet encryption key and wallet
wait    - start in loop mode: wait-mount-sign-unmount-wait


                             USAGE NOTES

If invoked with no command, the program mounts a removable device containing
unsigned MMGen transactions and/or message files, signs them, unmounts the
removable device and exits.

If invoked with 'wait', the program waits in a loop, mounting the removable
device, performing signing operations and unmounting the device every time it
is inserted.

On supported platforms (currently Orange Pi, Rock Pi and Raspberry Pi boards),
the status LED indicates whether the program is busy or in standby mode, i.e.
ready for device insertion or removal.

The removable device must have a partition labeled MMGEN_TX with a user-
writable root directory and a directory named '/tx', where unsigned MMGen
transactions are placed. Optionally, the directory '/msg' may also be created
and unsigned message files created by `mmgen-msg` placed in this directory.

On the signing machine the mount point (currently configured as {asi.mountpoint!r})
must exist and /etc/fstab must contain the following entry:

    LABEL='MMGEN_TX' /mnt/tx auto noauto,user 0 0

Transactions are signed with a wallet on the signing machine located in the wallet
directory (currently configured as {asi.wallet_dir!r}) encrypted with a 64-character
hexadecimal password saved in the file `autosign.key` in the root of the removable
device partition.

The password and wallet can be created in one operation by invoking the
command with 'setup' with the removable device inserted.  In this case, the
user will be prompted for a seed mnemonic.

Alternatively, the password and wallet can be created separately by first
invoking the command with 'gen_key' and then creating and encrypting the
wallet using the -P (--passwd-file) option:

    $ mmgen-walletconv -r0 -q -iwords -d{asi.wallet_dir} -p1 -P/mnt/tx/autosign.key -Llabel

Note that the hash preset must be '1'.  Multiple wallets are permissible.

For good security, it's advisable to re-generate a new wallet and key for
each signing session.

This command is currently available only on Linux-based platforms.
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

cfg = Config(
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

type(cfg)._set_ok += ('outdir','passwd_file')

from .autosign import Autosign
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
