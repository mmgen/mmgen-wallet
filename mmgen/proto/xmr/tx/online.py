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
proto.xmr.tx.online: Monero online signed transaction class
"""

from .completed import Completed

class OnlineSigned(Completed):

	async def compat_send(self):
		from ....xmrwallet import op as xmrwallet_op
		op = xmrwallet_op('submit', self.cfg, self.filename, None, compat_call=True)
		await op.restart_wallet_daemon()
		return await op.main()

class Sent(OnlineSigned):
	pass

class AutomountOnlineSigned(OnlineSigned):
	pass

class AutomountSent(AutomountOnlineSigned):
	pass
