# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
xmrwallet.file: Monero file base class for the MMGen Suite
"""

import json
from ...util import make_chksum_N
from ...fileutil import get_data_from_file
from ...rpc.util import json_encoder

class MoneroMMGenFile:

	silent_load = False

	def make_chksum(self, *, keys=None):
		res = json.dumps(
			{k: v for k, v in self.data._asdict().items() if (not keys or k in keys)},
			cls = json_encoder)
		return make_chksum_N(res, rounds=1, nchars=self.chksum_nchars, upper=False)

	@property
	def base_chksum(self):
		return self.make_chksum(keys=self.base_chksum_fields)

	@property
	def full_chksum(self):
		return self.make_chksum(keys=self.full_chksum_fields) if self.full_chksum_fields else None

	def check_checksums(self, d_wrap):
		for k in ('base_chksum', 'full_chksum'):
			a = getattr(self, k)
			if a is not None:
				b = d_wrap[k]
				assert a == b, f'{k} mismatch: {a} != {b}'

	def make_json_data(self, *, delete_metadata=True):
		return json.dumps(
			{self.data_label: self.make_outer_data(delete_metadata=delete_metadata)},
			cls = json_encoder,
			indent = 2)

	def make_outer_data(self, *, delete_metadata=True):
		return {
			'base_chksum': self.base_chksum,
			'full_chksum': self.full_chksum,
			'data': self.data._asdict() | ({'metadata': None} if delete_metadata else {})
		} if self.full_chksum else {
			'base_chksum': self.base_chksum,
			'data': self.data._asdict() | ({'metadata': None} if delete_metadata else {})}

	def extract_data_from_file(self, cfg, fn):
		data = json.loads(get_data_from_file(cfg, str(fn), desc=self.desc, silent=self.silent_load))
		return data.get(self.data_label) or data['MMGenTransaction'][self.data_label]
