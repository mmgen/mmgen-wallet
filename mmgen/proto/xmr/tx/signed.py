# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.xmr.tx.signed: Monero signed transaction class
"""

from ....tx import signed as TxBase
from .completed import Completed

class Signed(Completed, TxBase.Signed):

	def parse_txfile_serialized_data(self):
		pass

class AutomountSigned(Signed):
	desc = 'signed automount transaction'
	ext = 'asigtx'
