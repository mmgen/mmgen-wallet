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
-h, --help       Print this help message
--, --longhelp   Print help message for long (global) options
-a, --autosign   Send an autosigned transaction created by ‘mmgen-txcreate
                 --autosign’.  The removable device is mounted and unmounted
                 automatically. The transaction file argument must be omitted
                 when using this option
-A, --abort      Abort an unsent transaction created by ‘mmgen-txcreate
                 --autosign’ and delete it from the removable device.  The
                 transaction may be signed or unsigned.
-d, --outdir=d   Specify an alternate directory 'd' for output
-H, --dump-hex=F Instead of sending to the network, dump the transaction hex
                 to file ‘F’.  Use filename ‘-’ to dump to standard output.
-m, --mark-sent  Mark the transaction as sent by adding it to the removable
                 device.  Used in combination with --autosign when a trans-
                 action has been successfully sent out-of-band.
-n, --tx-proxy=P Send transaction via public TX proxy ‘P’ (supported proxies:
                 {tx_proxies}).  This is done via a publicly accessible web
                 page, so no API key or registration is required.
-q, --quiet      Suppress warnings; overwrite files without prompting
-r, --receipt    Print the receipt of the sent transaction (Ethereum only)
-s, --status     Get status of a sent transaction (or current transaction,
                 whether sent or unsent, when used with --autosign)
-t, --test       Test whether the transaction can be sent without sending it
-T, --txhex-idx=N Send only part ‘N’ of a multi-part transaction.  Indexing
                 begins with one.
-v, --verbose    Be more verbose
-w, --wait       Wait for transaction confirmation (Ethereum only)
-x, --proxy=P    Connect to TX proxy via SOCKS5h proxy ‘P’ (host:port).
                 Use special value ‘env’ to honor *_PROXY environment vars
                 instead.
-y, --yes        Answer 'yes' to prompts, suppress non-essential output
"""
	},
	'code': {
		'options': lambda cfg, proto, help_notes, s: s.format(
			tx_proxies = help_notes('tx_proxies'))
	}
}

cfg = Config(opts_data=opts_data)

if cfg.autosign and cfg.outdir:
	die(1, '--outdir cannot be used in combination with --autosign')

if cfg.mark_sent and not cfg.autosign:
	die(1, '--mark-sent is used only in combination with --autosign')

if cfg.test and cfg.dump_hex:
	die(1, '--test cannot be used in combination with --dump-hex')

if cfg.dump_hex and cfg.dump_hex != '-':
	from .fileutil import check_outfile_dir
	check_outfile_dir(cfg.dump_hex)

asi = None

match cfg._args:
	case [infile]:
		from .fileutil import check_infile
		check_infile(infile)
	case [] if cfg.autosign:
		from .tx.util import mount_removable_device
		from .autosign import Signable
		asi = mount_removable_device(cfg)
		si = Signable.automount_transaction(asi)
		if cfg.abort:
			si.shred_abortable() # prompts user, then raises exception or exits
		elif cfg.status or cfg.receipt:
			if si.unsent:
				die(1, 'Transaction is unsent')
			if si.unsigned:
				die(1, 'Transaction is unsigned')
		else:
			infile = si.get_unsent()
			cfg._util.qmsg(f'Got signed transaction file ‘{infile}’')
	case _:
		cfg._usage()

if not cfg.status:
	from .ui import do_license_msg
	do_license_msg(cfg)

from .tx import OnlineSignedTX

async def main():

	global cfg

	if (cfg.status or cfg.receipt) and cfg.autosign:
		tx = await si.get_last_created()
	else:
		tx = await OnlineSignedTX(
			cfg        = cfg,
			filename   = infile,
			automount  = cfg.autosign,
			quiet_open = True)

	if tx.is_compat:
		return await tx.compat_send()

	cfg = Config({'_clone': cfg, 'proto': tx.proto, 'coin': tx.proto.coin})

	if cfg.tx_proxy:
		from .tx.tx_proxy import check_client
		check_client(cfg)

	from .rpc import rpc_init
	tx.rpc = await rpc_init(cfg)

	cfg._util.vmsg(f'Getting {tx.desc} ‘{tx.infile}’')

	if cfg.mark_sent:
		await tx.post_send(asi)
		sys.exit(0)

	if not (cfg.status or cfg.receipt):
		if tx.is_swap and not tx.check_swap_expiry():
			die(1, 'Swap quote has expired. Please re-create the transaction')

		if not cfg.yes:
			tx.info.view_with_prompt('View transaction details?')
			if tx.add_comment(): # edits an existing comment, returns true if changed
				if not cfg.autosign:
					tx.file.write(ask_write_default_yes=True)

	await tx.send(cfg, asi)

async_run(cfg, main)
