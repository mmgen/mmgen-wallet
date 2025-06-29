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
proto.eth.msg: Ethereum base protocol message signing classes
"""

from ...msg import coin_msg

class coin_msg(coin_msg):

	include_pubhash = False
	sigdata_pfx = '0x'
	msghash_types = ('eth_sign', 'raw') # first-listed is the default

	class unsigned(coin_msg.unsigned):

		async def do_sign(self, wif, message, msghash_type):
			from .util import ec_sign_message_with_privkey
			return ec_sign_message_with_privkey(self.cfg, message, bytes.fromhex(wif), msghash_type)

	class signed_online(coin_msg.signed_online):

		async def do_verify(self, addr, sig, message, msghash_type):
			from ...tool.coin import tool_cmd
			from .util import ec_recover_pubkey
			return tool_cmd(
				self.cfg,
				proto = self.proto).pubhex2addr(
					ec_recover_pubkey(self.cfg, message, sig, msghash_type)) == addr

	class exported_sigs(coin_msg.exported_sigs, signed_online):
		pass
