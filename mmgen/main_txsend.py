#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
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

from .common import *

opts_data = {
	'sets': [('yes', True, 'quiet', True)],
	'text': {
		'desc':    'Send a signed {pnm} cryptocoin transaction'.format(pnm=g.proj_name),
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

cmd_args = opts.init(opts_data)

rpc_init()

if len(cmd_args) == 1:
	infile = cmd_args[0]; check_infile(infile)
else:
	opts.usage()

if not opt.status:
	do_license_msg()

from .tx import *

tx = MMGenTX(infile,quiet_open=True) # sig check performed here
vmsg("Signed transaction file '{}' is valid".format(infile))

if not tx.marked_signed():
	die(1,'Transaction is not signed!')

if opt.status:
	if tx.coin_txid: qmsg('{} txid: {}'.format(g.coin,tx.coin_txid.hl()))
	tx.get_status(status=True)
	sys.exit(0)

if not opt.yes:
	tx.view_with_prompt('View transaction data?')
	if tx.add_comment(): # edits an existing comment, returns true if changed
		tx.write_to_file(ask_write_default_yes=True)

tx.send(exit_on_fail=True)
tx.write_to_file(ask_overwrite=False,ask_write=False)
tx.print_contract_addr()
