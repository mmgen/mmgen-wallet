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
mmgen-txsend: Broadcast a transaction signed by 'mmgen-txsign' to the network
"""

import sys

from .cfg import gc, Config
from .util import async_run, die

opts_data = {
	'sets': [
		('yes', True, 'quiet', True),
		('abort', True, 'autosign', True),
	],
	'text': {
		'desc':    f'Send a signed {gc.proj_name} cryptocoin transaction',
		'usage':   '[opts] [signed transaction file]',
		'options': """
-h, --help      Print this help message
--, --longhelp  Print help message for long (global) options
-a, --autosign  Send an autosigned transaction created by ‘mmgen-txcreate
                --autosign’.  The removable device is mounted and unmounted
                automatically. The transaction file argument must be omitted
                when using this option
-A, --abort     Abort an unsent transaction created by ‘mmgen-txcreate
                --autosign’ and delete it from the removable device.  The
                transaction may be signed or unsigned.
-d, --outdir= d Specify an alternate directory 'd' for output
-q, --quiet     Suppress warnings; overwrite files without prompting
-s, --status    Get status of a sent transaction (or the current transaction,
                whether sent or unsent, when used with --autosign)
-v, --verbose   Be more verbose
-y, --yes       Answer 'yes' to prompts, suppress non-essential output
"""
	}
}

cfg = Config(opts_data=opts_data)

if cfg.autosign and cfg.outdir:
	die(1, '--outdir cannot be used in combination with --autosign')

if len(cfg._args) == 1:
	infile = cfg._args[0]
	from .fileutil import check_infile
	check_infile(infile)
elif not cfg._args and cfg.autosign:
	from .tx.util import mount_removable_device
	from .autosign import Signable
	asi = mount_removable_device(cfg)
	si = Signable.automount_transaction(asi)
	if cfg.abort:
		si.shred_abortable() # prompts user, then raises exception or exits
	elif cfg.status:
		if si.unsent:
			die(1, 'Transaction is unsent')
		if si.unsigned:
			die(1, 'Transaction is unsigned')
	else:
		infile = si.get_unsent()
		cfg._util.qmsg(f'Got signed transaction file ‘{infile}’')
else:
	cfg._usage()

if not cfg.status:
	from .ui import do_license_msg
	do_license_msg(cfg)

async def main():

	from .tx import OnlineSignedTX, SentTX

	if cfg.status and cfg.autosign:
		tx = await si.get_last_created()
	else:
		tx = await OnlineSignedTX(
			cfg        = cfg,
			filename   = infile,
			automount  = cfg.autosign,
			quiet_open = True)

	from .rpc import rpc_init
	tx.rpc = await rpc_init(cfg, tx.proto)

	cfg._util.vmsg(f'Getting {tx.desc} ‘{tx.infile}’')

	if cfg.status:
		if tx.coin_txid:
			cfg._util.qmsg(f'{tx.proto.coin} txid: {tx.coin_txid.hl()}')
		await tx.status.display(usr_req=True)
		sys.exit(0)

	if not cfg.yes:
		tx.info.view_with_prompt('View transaction details?')
		if tx.add_comment(): # edits an existing comment, returns true if changed
			if not cfg.autosign:
				tx.file.write(ask_write_default_yes=True)

	if await tx.send():
		tx2 = await SentTX(cfg=cfg, data=tx.__dict__, automount=cfg.autosign)
		tx2.file.write(
			outdir        = asi.txauto_dir if cfg.autosign else None,
			ask_overwrite = False,
			ask_write     = False)
		tx2.print_contract_addr()

async_run(main())
