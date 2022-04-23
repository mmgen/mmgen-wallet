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
base_proto.bitcoin.msg: Bitcoin base protocol message signing classes
"""

from ...msg import coin_msg

class coin_msg(coin_msg):

	class base(coin_msg.base): pass

	class new(base,coin_msg.new): pass

	class completed(base,coin_msg.completed): pass

	class unsigned(completed,coin_msg.unsigned):

		async def do_sign(self,wif,message):
			return await self.rpc.call( 'signmessagewithprivkey', wif, message )

	class signed(completed,coin_msg.signed): pass

	class signed_online(signed,coin_msg.signed_online):

		async def do_verify(self,addr,sig,message):
			return await self.rpc.call( 'verifymessage', addr, sig, message )