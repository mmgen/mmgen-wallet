# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.xmr.addrdata: Monero AddrData and related classes
"""

from ...base_obj import AsyncInit
from ...addrdata import AddrData
from ...tw.addresses import TwAddresses

class MoneroTwAddrData(AddrData, metaclass=AsyncInit):

	async def __init__(self, cfg, proto, *, twctl=None):
		twaddrs = await TwAddresses(cfg, proto, add_twctl=False)
		rpc_data = await twaddrs.get_rpc_data()
		self.data = {k: v['addr'] for k, v in rpc_data.items()}

	def mmaddr2coinaddr(self, mmaddr):
		return self.data.get(mmaddr)
