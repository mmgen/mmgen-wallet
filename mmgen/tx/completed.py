#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
tx.completed: completed transaction class
"""

from .base import Base

class Completed(Base):
	"""
	signed or unsigned transaction with associated file
	"""
	filename_api = True

	def __init__(self, cfg, *args, filename=None, data=None, quiet_open=False, **kwargs):

		assert (filename or data) and not (filename and data), 'CompletedTX_chk1'

		super().__init__(cfg=cfg, *args, **kwargs)

		if data:
			self.__dict__ = data | {'twctl': self.twctl}
			self.name = type(self).__name__
		else:
			from .file import MMGenTxFile
			MMGenTxFile(self).parse(str(filename), quiet_open=quiet_open)

			self.check_serialized_integrity()

			# repeat with sign and send, because coin daemon could be restarted
			self.check_correct_chain()

			if self.check_sigs() != self.signed:
				from ..util import die
				die(1, 'Transaction is {}signed!'.format('not ' if self.signed else ''))

			self.infile = filename

	@property
	def file(self):
		from .file import MMGenTxFile
		return MMGenTxFile(self)

	@staticmethod
	def ext_to_cls(ext, proto):
		"""
		see twctl:import_token()
		"""
		from .unsigned import Unsigned, AutomountUnsigned
		from .online import Sent, AutomountSent
		for cls in (Unsigned, AutomountUnsigned, Sent, AutomountSent):
			if ext == getattr(cls, 'ext'):
				return cls

		if proto.tokensym:
			from .online import OnlineSigned as Signed
			from .online import AutomountOnlineSigned as AutomountSigned
		else:
			from .signed import Signed, AutomountSigned
		for cls in (Signed, AutomountSigned):
			if ext == getattr(cls, 'ext'):
				return cls

	def check_swap_memo(self):
		if data := self.get_tx_usr_data():
			from ..swap.proto.thorchain.memo import Memo
			if Memo.is_partial_memo(data):
				from ..protocol import init_proto
				text = data.decode('ascii')
				p = Memo.parse(text)
				assert p.function == 'SWAP', f'‘{p.function}’: unsupported function in swap memo ‘{text}’'
				assert p.chain == p.asset, f'{p.chain} != {p.asset}: chain/asset mismatch in swap memo ‘{text}’'
				proto = init_proto(self.cfg, p.asset, network=self.cfg.network, need_amt=True)
				if self.swap_recv_addr_mmid:
					mmid = self.swap_recv_addr_mmid
				elif self.cfg.allow_non_wallet_swap:
					from ..util import ymsg
					ymsg('Warning: allowing swap to non-wallet address (--allow-non-wallet-swap)')
					mmid = None
				else:
					raise ValueError('Swap to non-wallet address forbidden (override with --allow-non-wallet-swap)')
				return self.Output(proto, addr=p.address, mmid=mmid, amt=proto.coin_amt('0'))
