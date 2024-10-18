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
