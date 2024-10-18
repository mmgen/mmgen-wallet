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
xmrwallet.ops.import: Monero wallet ops for the MMGen Suite
"""

from ...util import msg, bmsg, die, suf

from ..file.outputs import MoneroWalletOutputsFile
from ..rpc import MoneroWalletRPC

from .wallet import OpWallet

class OpImportOutputs(OpWallet):
	action = 'importing wallet outputs into'
	start_daemon = False

	async def main(self, fn, wallet_idx, restart_daemon=True):
		if restart_daemon:
			await self.restart_wallet_daemon()
		h = MoneroWalletRPC(self, self.addr_data[0])
		self.head_msg(wallet_idx, fn)
		if restart_daemon:
			h.open_wallet(refresh=False)
		m = MoneroWalletOutputsFile.Unsigned(
			parent = self,
			fn     = fn)
		res = self.c.call(
			'import_outputs',
			outputs_data_hex = m.data.outputs_data_hex)
		idata = res['num_imported']
		bmsg(f'\n  {idata} output{suf(idata)} imported')
		if m.data.sign:
			data = m.data._asdict()
			data.update(self.c.call('export_key_images', all=True))
			m = MoneroWalletOutputsFile.SignedNew(
				parent    = self,
				wallet_fn = m.get_wallet_fn(fn),
				data      = data)
			idata = m.data.signed_key_images or []
			bmsg(f'  {len(idata)} key image{suf(idata)} signed')
		else:
			m.data = m.data._replace(imported=True)
		return m

class OpImportKeyImages(OpWallet):
	action = 'importing key images into'
	stem = 'process'
	trust_monerod = True

	def post_main_failure(self):
		rw_msg = ' for requested wallets' if self.uargs.wallets else ''
		die(2, f'No signed key image files found{rw_msg}!')

	async def process_wallet(self, d, fn, last):
		keyimage_fn = MoneroWalletOutputsFile.Signed.find_fn_from_wallet_fn(self.cfg, fn, ret_on_no_match=True)
		if not keyimage_fn:
			msg(f'No signed key image file found for wallet #{d.idx}')
			return False
		h = MoneroWalletRPC(self, d)
		h.open_wallet()
		self.head_msg(d.idx, h.fn)
		m = MoneroWalletOutputsFile.Signed(parent=self, fn=keyimage_fn)
		data = m.data.signed_key_images or []
		bmsg(f'\n  {len(data)} signed key image{suf(data)} to import')
		if data:
			res = self.c.call('import_key_images', signed_key_images=data)
			bmsg(f'  Success: {res}')
		return True
