#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
tx.completed: completed transaction class
"""

from .base import Base

class Completed(Base):
	"""
	signed or unsigned transaction with associated file
	"""
	filename_api = True

	def __init__(self,filename=None,data=None,quiet_open=False,*args,**kwargs):

		assert (filename or data) and not (filename and data), 'CompletedTX_chk1'

		super().__init__(*args,**kwargs)

		if data:
			data['tw'] = self.tw
			self.__dict__ = data
			self.name = type(self).__name__
		else:
			from ..txfile import MMGenTxFile
			MMGenTxFile(self).parse(filename,quiet_open=quiet_open)

			self.check_serialized_integrity()

			# repeat with sign and send, because coin daemon could be restarted
			self.check_correct_chain()

			if self.check_sigs() != self.signed:
				die(1,'Transaction is {}signed!'.format('not' if self.signed else ''))

	@property
	def info(self):
		from .info import init_info
		return init_info(self)

	@property
	def file(self):
		from ..txfile import MMGenTxFile
		return MMGenTxFile(self)

	@classmethod
	def ext_to_type(cls,ext,proto):
		"""
		see twctl:import_token()
		"""
		from .unsigned import Unsigned
		if ext == Unsigned.ext:
			return Unsigned

		if proto.tokensym:
			from .online import OnlineSigned as Signed
		else:
			from .signed import Signed
		if ext == Signed.ext:
			return Signed
