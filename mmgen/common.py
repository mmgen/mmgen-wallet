#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
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
common.py:  Common imports for all MMGen scripts
"""

import sys,os
from mmgen.exception import *
from mmgen.globalvars import g
import mmgen.opts as opts
from mmgen.opts import opt
from mmgen.util import *

def set_debug_all():
	if os.getenv('MMGEN_DEBUG_ALL'):
		for name in g.env_opts:
			if name[:11] == 'MMGEN_DEBUG':
				os.environ[name] = '1'

def help_notes(k):
	from mmgen.seed import SeedSource
	from mmgen.tx import MMGenTX
	def fee_spec_letters(use_quotes=False):
		cu = g.proto.coin_amt.units
		sep,conj = ((',',' or '),("','","' or '"))[use_quotes]
		return sep.join(u[0] for u in cu[:-1]) + ('',conj)[len(cu)>1] + cu[-1][0]
	def fee_spec_names():
		cu = g.proto.coin_amt.units
		return ', '.join(cu[:-1]) + ('',' and ')[len(cu)>1] + cu[-1] + ('',',\nrespectively')[len(cu)>1]
	return {
		'rel_fee_desc': MMGenTX().rel_fee_desc,
		'fee_spec_letters': fee_spec_letters(),
		'passwd': """
For passphrases all combinations of whitespace are equal, and leading and
trailing space are ignored.  This permits reading passphrase or brainwallet
data from a multi-line file with free spacing and indentation.
""".strip(),
		'brainwallet': """
BRAINWALLET NOTE:

To thwart dictionary attacks, it's recommended to use a strong hash preset
with brainwallets.  For a brainwallet passphrase to generate the correct
seed, the same seed length and hash preset parameters must always be used.
""".strip(),
		'txcreate': """
The transaction's outputs are specified on the command line, while its inputs
are chosen from a list of the user's unpent outputs via an interactive menu.

If the transaction fee is not specified on the command line (see FEE
SPECIFICATION below), it will be calculated dynamically using network fee
estimation for the default (or user-specified) number of confirmations.
If network fee estimation fails, the user will be prompted for a fee.

Network-estimated fees will be multiplied by the value of '--tx-fee-adj',
if specified.

Ages of transactions are approximate based on an average block discovery
interval of one per {g.proto.secs_per_block} seconds.

All addresses on the command line can be either {pnu} addresses or {pnm}
addresses of the form <seed ID>:<index>.

To send the value of all inputs (minus TX fee) to a single output, specify
one address with no amount on the command line.
""".format(g=g,pnm=g.proj_name,pnu=g.proto.name.capitalize()),
		'fee': """
FEE SPECIFICATION: Transaction fees, both on the command line and at the
interactive prompt, may be specified as either absolute {c} amounts, using
a plain decimal number, or as {r}, using an integer followed by
'{l}', for {u}.
""".format( c=g.coin,
			r=MMGenTX().rel_fee_desc,
			l=fee_spec_letters(use_quotes=True),
			u=fee_spec_names() ),
		'txsign': """
Transactions may contain both {pnm} or non-{pnm} input addresses.

To sign non-{pnm} inputs, a {dn} wallet dump or flat key list is used
as the key source ('--keys-from-file' option).

To sign {pnm} inputs, key data is generated from a seed as with the
{pnl}-addrgen and {pnl}-keygen commands.  Alternatively, a key-address file
may be used (--mmgen-keys-from-file option).

Multiple wallets or other seed files can be listed on the command line in
any order.  If the seeds required to sign the transaction's inputs are not
found in these files (or in the default wallet), the user will be prompted
for seed data interactively.

To prevent an attacker from crafting transactions with bogus {pnm}-to-{pnu}
address mappings, all outputs to {pnm} addresses are verified with a seed
source.  Therefore, seed files or a key-address file for all {pnm} outputs
must also be supplied on the command line if the data can't be found in the
default wallet.

Seed source files must have the canonical extensions listed in the 'FileExt'
column below:

  {n_fmt}
""".format( dn=g.proto.daemon_name,
			n_fmt='\n  '.join(SeedSource.format_fmt_codes().splitlines()),
			pnm=g.proj_name,
			pnu=g.proto.name.capitalize(),
			pnl=g.proj_name.lower())
	}[k] + ('-α' if g.debug_utf8 else '')
