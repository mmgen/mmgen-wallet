#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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
tx-btc2bch: Convert MMGen transaction files from BTC to BCH format
"""

from mmgen.common import *

opts_data = lambda: {
	'desc': """Convert {pnm} transaction files from BTC to BCH format""".format(pnm=g.proj_name),
	'usage':'[opts] [mmgen transaction file]',
	'options': """
-h, --help         Print this help message
--, --longhelp     Print help message for long options (common options)
-v, --verbose      Produce more verbose output
"""
}

cmd_args = opts.init(opts_data)

if g.coin != 'BTC':
	die(1,"This program must be run with --coin set to 'BTC'")

if len(cmd_args) != 1: opts.usage()

import mmgen.tx
tx = mmgen.tx.MMGenTX(cmd_args[0])

if opt.verbose:
	gmsg('Original transaction is in {} format'.format(g.coin))

from mmgen.protocol import init_coin
init_coin('BCH')

reload(sys.modules['mmgen.tx'])

if opt.verbose:
	gmsg('Converting transaction to {} format'.format(g.coin))

tx.inputs.convert_coin(verbose=opt.verbose)
tx.outputs.convert_coin(verbose=opt.verbose)

tx.desc = 'converted transaction'
tx.write_to_file(ask_write=False,ask_overwrite=False)
