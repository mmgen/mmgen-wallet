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
base_proto.ethereum.msg: Ethereum base protocol message signing classes
"""

from ...msg import coin_msg

class coin_msg(coin_msg):

	class base(coin_msg.base): pass

	class new(base,coin_msg.new): pass

	class completed(base,coin_msg.completed): pass

	class unsigned(completed,coin_msg.unsigned):

		async def do_sign(self,wif,message,msghash_type):
			from .misc import ec_sign_message_with_privkey
			return ec_sign_message_with_privkey( message, bytes.fromhex(wif), msghash_type )

	class signed(completed,coin_msg.signed): pass

	class signed_online(signed,coin_msg.signed_online):

		async def do_verify(self,addr,sig,message,msghash_type):
			from ...tool.coin import tool_cmd
			from .misc import ec_recover_pubkey
			return tool_cmd(proto=self.proto).pubhex2addr(ec_recover_pubkey( message, sig, msghash_type )) == addr

	class exported_sigs(coin_msg.exported_sigs,signed_online): pass
