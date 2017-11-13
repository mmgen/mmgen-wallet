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
mmgen-txcreate: Create a cryptocoin transaction with MMGen- and/or non-MMGen
                inputs and outputs
"""

from mmgen.common import *

opts_data = lambda: {
	'desc': 'Create a transaction with outputs to specified coin or {g.proj_name} addresses'.format(g=g),
	'usage':   '[opts]  <addr,amt> ... [change addr] [addr file] ...',
	'sets': ( ('yes', True, 'quiet', True), ),
	'options': """
-h, --help           Print this help message
--, --longhelp       Print help message for long options (common options)
-a, --tx-fee-adj=  f Adjust transaction fee by factor 'f' (see below)
-B, --no-blank       Don't blank screen before displaying unspent outputs
-c, --comment-file=f Source the transaction's comment from file 'f'
-C, --tx-confs=    c Desired number of confirmations (default: {g.tx_confs})
-d, --outdir=      d Specify an alternate directory 'd' for output
-f, --tx-fee=      f Transaction fee, as a decimal {cu} amount or in satoshis
                     per byte (an integer followed by 's').  If omitted, fee
                     will be calculated using {dn}'s 'estimatefee' call
-i, --info           Display unspent outputs and exit
-L, --locktime=    t Lock time (block height or unix seconds) (default: 0)
-m, --minconf=     n Minimum number of confirmations required to spend
                     outputs (default: 1)
-q, --quiet          Suppress warnings; overwrite files without prompting
-r, --rbf            Make transaction BIP 125 replaceable (replace-by-fee)
-v, --verbose        Produce more verbose output
-y, --yes            Answer 'yes' to prompts, suppress non-essential output
""".format(g=g,cu=g.coin,dn=g.proto.daemon_name),
	'notes': '\n' + help_notes('txcreate') + help_notes('fee')
}

cmd_args = opts.init(opts_data)

rpc_init()

from mmgen.tx import MMGenTX
tx = MMGenTX()
tx.create(cmd_args,int(opt.locktime or 0),do_info=opt.info)
tx.write_to_file(ask_write=not opt.yes,ask_overwrite=not opt.yes,ask_write_default_yes=False)
