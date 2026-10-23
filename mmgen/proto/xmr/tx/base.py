# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.xmr.tx.base: Monero base transaction class
"""

class Base:
	is_compat = True
	has_comment = False
	compat_data_label = 'MoneroMMGenTX'
	raw_compat_data = None

	@property
	def nondata_outputs(self):
		return ()

	def is_replaceable(self):
		return False

	def get_serialized_locktime(self):
		return None

	def check_serialized_integrity(self):
		pass

	def check_sigs(self):
		return bool(getattr(self.compat_tx.data, 'signed_txset', None))

	def add_sent_timestamp(self):
		pass

	def add_blockcount(self):
		pass
