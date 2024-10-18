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
tx.online: online signed transaction class
"""

from .signed import Signed, AutomountSigned

class OnlineSigned(Signed):

	@property
	def status(self):
		from . import _base_proto_subclass
		return _base_proto_subclass('Status', 'status', self.proto)(self)

	def confirm_send(self):
		from ..util import msg
		from ..ui import confirm_or_raise
		confirm_or_raise(
			cfg     = self.cfg,
			message = '' if self.cfg.quiet else 'Once this transaction is sent, there’s no taking it back!',
			action  = f'broadcast this transaction to the {self.proto.coin} {self.proto.network.upper()} network',
			expect  = 'YES' if self.cfg.quiet or self.cfg.yes else 'YES, I REALLY WANT TO DO THIS')
		msg('Sending transaction')

class AutomountOnlineSigned(AutomountSigned, OnlineSigned):
	pass

class Sent(OnlineSigned):
	desc = 'sent transaction'
	ext = 'subtx'

class AutomountSent(AutomountOnlineSigned):
	desc = 'sent automount transaction'
	ext = 'asubtx'
