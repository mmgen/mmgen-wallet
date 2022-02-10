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
base_proto.bitcoin.twctl: Bitcoin base protocol tracking wallet control class
"""

from ....tw.ctl import TrackingWallet
from ....util import rmsg,write_mode

class BitcoinTrackingWallet(TrackingWallet):

	def init_empty(self):
		self.data = { 'coin': self.proto.coin, 'addresses': {} }

	def upgrade_wallet_maybe(self):
		pass

	async def rpc_get_balance(self,addr):
		raise NotImplementedError('not implemented')

	@write_mode
	async def import_address(self,addr,label,rescan):
		return await self.rpc.call('importaddress',addr,label,rescan,timeout=(False,3600)[rescan])

	@write_mode
	def batch_import_address(self,arg_list):
		return self.rpc.batch_call('importaddress',arg_list)

	@write_mode
	async def remove_address(self,addr):
		raise NotImplementedError(f'address removal not implemented for coin {self.proto.coin}')

	@write_mode
	async def set_label(self,coinaddr,lbl):
		args = self.rpc.daemon.set_label_args( self.rpc, coinaddr, lbl )
		try:
			return await self.rpc.call(*args)
		except Exception as e:
			rmsg(e.args[0])
			return False
