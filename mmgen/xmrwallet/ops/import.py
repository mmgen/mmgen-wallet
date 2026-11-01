# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
xmrwallet.ops.import: Monero wallet ops for the MMGen Suite
"""
from pathlib import Path

from ...util import msg, bmsg, die, suf

from ..file.outputs import MoneroWalletOutputsFile
from ..rpc import MoneroWalletRPC

from .wallet import OpWallet

class OpImportOutputs(OpWallet):
	action = 'importing wallet outputs into'
	stem = 'process'
	return_data = True
	main_starts_daemon = True

	async def process_wallet(self, d, fn, last):
		h = MoneroWalletRPC(self, d)
		h.open_wallet(refresh=False)
		self.head_msg(d.idx, h.fn)
		outputs_file = Path(self.uargs.spec)
		m = MoneroWalletOutputsFile.Unsigned(parent=self, fn=outputs_file)
		res = self.c.call(
			'import_outputs',
			outputs_data_hex = m.data.outputs_data_hex)
		count = res['num_imported']
		bmsg(f'\n  {count} output{suf(count)} imported')
		if m.data.sign:
			data = m.data._asdict()
			data.update(self.c.call('export_key_images', all=True))
			m = MoneroWalletOutputsFile.SignedNew(
				parent    = self,
				wallet_fn = m.get_wallet_fn(outputs_file),
				data      = data)
			kdata = m.data.signed_key_images or []
			bmsg(f'  {len(kdata)} key image{suf(kdata)} signed')
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
		keyimage_fn = MoneroWalletOutputsFile.Signed.find_fn_from_wallet_fn(
			self.cfg,
			fn,
			wallet_dir = None if self.cfg.autosign else self.wd.wallet_dir,
			ret_on_no_match = True)
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
