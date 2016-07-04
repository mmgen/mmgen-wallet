#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2016 Philemon <mmgen-py@yandex.com>
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
	'options': """
-h, --help      Print this help message
-d, --outdir= d Specify an alternate directory 'd' for output
-q, --quiet     Suppress warnings; overwrite files without prompting
"""
}

cmd_args = opts.init(opts_data)

if len(cmd_args) == 1:
	infile = cmd_args[0]; check_infile(infile)
else: opts.usage()

# Begin execution

do_license_msg()

tx = MMGenTX()

tx.parse_tx_file(infile,'signed transaction data')

c = bitcoin_connection()

if not tx.check_signed(c):
	die(1,'Transaction has no signature!')

qmsg("Signed transaction file '%s' is valid" % infile)

tx.view_with_prompt('View transaction data?')

if tx.add_comment(): # edits an existing comment, returns true if changed
	tx.write_to_file(ask_write_default_yes=True)

warn   = "Once this transaction is sent, there's no taking it back!"
action = 'broadcast this transaction to the network'
expect = 'YES, I REALLY WANT TO DO THIS'

if opt.quiet: warn,expect = '','YES'

confirm_or_exit(warn,action,expect)

msg('Sending transaction')

tx.send(c,bogus=True)

tx.write_txid_to_file()
