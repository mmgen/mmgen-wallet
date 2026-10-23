# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.xmr.tx.completed: Monero completed transaction class
"""

from ....util import cached_property, make_timestamp
from ....color import cyan
from ....tx.completed import Completed as TxCompleted

from .base import Base

class Completed(Base, TxCompleted):

	@cached_property
	def compat_tx(self):
		from ....xmrwallet.file.tx import MoneroMMGenTX
		if self.compat_data:
			return MoneroMMGenTX.ViewData(self.cfg, self.compat_data)
		elif self.raw_compat_data:
			return MoneroMMGenTX.Completed(self.cfg, None, compat_data=self.raw_compat_data)
		else:
			from pathlib import Path
			return MoneroMMGenTX.View(self.cfg, Path(self.infile))

	@cached_property
	def timestamp(self):
		return make_timestamp(self.compat_tx.data.create_time)

	@cached_property
	def sent_timestamp(self):
		return make_timestamp(self.compat_tx.data.submit_time)

	@property
	def info(self):
		from ....tx.info import TxInfo
		class info_cls(TxInfo):
			def format(info_self, *args, **kwargs):
				body = self.compat_tx.get_info(full_address=True, indent='  ', is_swap=self.is_swap)
				if self.compat_data or self.raw_compat_data:
					swap_subhdr = ''.join(info_self.gen_swap_subhdr()) + '\n' if self.is_swap else ''
					return cyan(self.data_desc.upper()) + '\n' + swap_subhdr + body
				else:
					return body
		return info_cls(self.cfg, self)
