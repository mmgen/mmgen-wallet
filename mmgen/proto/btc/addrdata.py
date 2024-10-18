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
proto.btc.addrdata: Bitcoin base protocol addrdata classes
"""

from ...addrdata import TwAddrData

class BitcoinTwAddrData(TwAddrData):

	msgs = {
		'multiple_acct_addrs': """
			ERROR: More than one address found for account: {acct!r}.
			Your 'wallet.dat' file appears to have been altered by a non-{proj} program.
			Please restore your tracking wallet from a backup or create a new one and
			re-import your addresses.
		"""
	}

	async def get_tw_data(self, twctl=None):
		self.cfg._util.vmsg('Getting address data from tracking wallet')
		c = self.rpc
		if 'label_api' in c.caps:
			accts = await c.call('listlabels')
			ll = await c.batch_call('getaddressesbylabel', [(k,) for k in accts])
			alists = [list(a.keys()) for a in ll]
		else:
			accts = await c.call('listaccounts', 0, True)
			alists = await c.batch_call('getaddressesbyaccount', [(k,) for k in accts])
		return list(zip(accts, alists))
