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
tx.online: online signed transaction class
"""

from .signed import Signed, AutomountSigned

class OnlineSigned(Signed):

	@property
	def status(self):
		from . import _base_proto_subclass
		return _base_proto_subclass('Status', 'status', self.proto)(self)

	def check_swap_expiry(self):
		import time
		from ..util import msg, make_timestr
		from ..util2 import format_elapsed_hr
		from ..color import pink, yellow
		expiry = self.swap_quote_expiry
		now = int(time.time())
		t_rem = expiry - now
		clr = yellow if t_rem < 0 else pink
		msg('Swap quote {a} {b} [{c}]'.format(
			a = clr('expired' if t_rem < 0 else 'expires'),
			b = clr(format_elapsed_hr(expiry, now=now, future_msg='from now')),
			c = make_timestr(expiry)))
		return t_rem >= 0

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
