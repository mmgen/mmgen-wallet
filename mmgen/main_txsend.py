#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
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

from .cfg import gc,Config
from .util import async_run

opts_data = {
	'sets': [('yes', True, 'quiet', True)],
	'text': {
		'desc':    f'Send a signed {gc.proj_name} cryptocoin transaction',
		'usage':   '[opts] <signed transaction file>',
		'options': """
-h, --help      Print this help message
--, --longhelp  Print help message for long options (common options)
-d, --outdir= d Specify an alternate directory 'd' for output
-q, --quiet     Suppress warnings; overwrite files without prompting
-s, --status    Get status of a sent transaction
-y, --yes       Answer 'yes' to prompts, suppress non-essential output
"""
	}
}

cfg = Config(opts_data=opts_data)

if len(cfg._args) == 1:
	infile = cfg._args[0]
	from .fileutil import check_infile
	check_infile(infile)
else:
	cfg._opts.usage()

if not cfg.status:
	from .ui import do_license_msg
	do_license_msg(cfg)

async def main():

	from .tx import OnlineSignedTX

	tx = await OnlineSignedTX(
		cfg        = cfg,
		filename   = infile,
		quiet_open = True)

	from .rpc import rpc_init
	tx.rpc = await rpc_init(cfg,tx.proto)

	cfg._util.vmsg(f'Signed transaction file {infile!r} is valid')

	if cfg.status:
		if tx.coin_txid:
			cfg._util.qmsg(f'{tx.proto.coin} txid: {tx.coin_txid.hl()}')
		await tx.status.display(usr_req=True)
		sys.exit(0)

	if not cfg.yes:
		tx.info.view_with_prompt('View transaction details?')
		if tx.add_comment(): # edits an existing comment, returns true if changed
			tx.file.write(ask_write_default_yes=True)

	await tx.send(exit_on_fail=True)
	tx.file.write(
		ask_overwrite = False,
		ask_write     = False)
	tx.print_contract_addr()

async_run(main())
