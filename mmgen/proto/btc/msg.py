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
proto.btc.msg: Bitcoin base protocol message signing classes
"""

from ...msg import coin_msg

class coin_msg(coin_msg):

	include_pubhash = True
	sigdata_pfx = None
	msghash_types = ('raw',) # first-listed is the default

	class unsigned(coin_msg.unsigned):

		async def do_sign(self, wif, message, msghash_type):
			return await self.rpc.call('signmessagewithprivkey', wif, message)

	class signed_online(coin_msg.signed_online):

		async def do_verify(self, addr, sig, message, msghash_type):
			return await self.rpc.call('verifymessage', addr, sig, message)

	class exported_sigs(coin_msg.exported_sigs, signed_online):
		pass
