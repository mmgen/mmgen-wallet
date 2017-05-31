#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2017 Philemon <mmgen-py@yandex.com>
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

from mmgen.common import *
from mmgen.tx import *

opts_data = {
	'desc':    'Send a Bitcoin transaction signed by {pnm}-txsign'.format(
					pnm=g.proj_name.lower()),
	'usage':   '[opts] <signed transaction file>',
	'sets': ( ('yes', True, 'quiet', True), ),
	'options': """
-h, --help      Print this help message
--, --longhelp  Print help message for long options (common options)
-d, --outdir= d Specify an alternate directory 'd' for output
-q, --quiet     Suppress warnings; overwrite files without prompting
-y, --yes       Answer 'yes' to prompts, suppress non-essential output
"""
}

cmd_args = opts.init(opts_data)

if len(cmd_args) == 1:
	infile = cmd_args[0]; check_infile(infile)
else: opts.usage()

do_license_msg()
tx = MMGenTX(infile)
c = bitcoin_connection()

if not tx.check_signed(c):
	die(1,'Transaction is not signed!')

if tx.btc_txid:
	msg('Warning: transaction has already been sent!')

qmsg("Signed transaction file '%s' is valid" % infile)

if not opt.yes:
	tx.view_with_prompt('View transaction data?')
	if tx.add_comment(): # edits an existing comment, returns true if changed
		tx.write_to_file(ask_write_default_yes=True)

if tx.send(c):
	tx.write_to_file(ask_overwrite=False,ask_write=False)
