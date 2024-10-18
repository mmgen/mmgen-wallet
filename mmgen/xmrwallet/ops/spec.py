#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
xmrwallet.ops.spec: Monero wallet ops for the MMGen Suite
"""

import re

from ...util import die
from ...addr import CoinAddr

from .. import uarg_info

class OpMixinSpec:

	def create_addr_data(self):
		m = re.fullmatch(uarg_info[self.spec_id].pat, self.uargs.spec, re.ASCII)
		if not m:
			fs = "{!r}: invalid {!r} arg: for {} operation, it must have format {!r}"
			die(1, fs.format(self.uargs.spec, self.spec_id, self.name, uarg_info[self.spec_id].annot))

		def gen():
			for i, k in self.spec_key:
				if m[i] is None:
					setattr(self, k, None)
				else:
					idx = int(m[i])
					try:
						res = self.kal.entry(idx)
					except:
						die(1, f'Supplied key-address file does not contain address {self.kal.al_id.sid}:{idx}')
					else:
						setattr(self, k, res)
						yield res

		self.addr_data = list(gen())
		self.account = None if m[2] is None else int(m[2])

		def strip_quotes(s):
			if s and s[0] in ("'", '"'):
				if s[-1] != s[0] or len(s) < 2:
					die(1, f'{s!r}: unbalanced quotes in label string!')
				return s[1:-1]
			else:
				return s # None or empty string

		if self.name in ('sweep', 'sweep_all'):
			self.dest_acct = None if m[4] is None else int(m[4])
		elif self.name == 'transfer':
			self.dest_addr = CoinAddr(self.proto, m[3])
			self.amount = self.proto.coin_amt(m[4])
		elif self.name == 'new':
			self.label = strip_quotes(m[3])
		elif self.name == 'label':
			self.address_idx = int(m[3])
			self.label = strip_quotes(m[4])
