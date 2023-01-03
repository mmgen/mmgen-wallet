#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
tx.online: online signed transaction class
"""

from .signed import Signed

class OnlineSigned(Signed):

	@property
	def status(self):
		from . import _base_proto_subclass
		return _base_proto_subclass('Status','status',self.proto)(self)

	def confirm_send(self):
		from ..opts import opt
		from ..util import msg
		from ..ui import confirm_or_raise
		confirm_or_raise(
			message = '' if opt.quiet else 'Once this transaction is sent, there’s no taking it back!',
			action  = f'broadcast this transaction to the {self.proto.coin} {self.proto.network.upper()} network',
			expect  = 'YES' if opt.quiet or opt.yes else 'YES, I REALLY WANT TO DO THIS' )
		msg('Sending transaction')
