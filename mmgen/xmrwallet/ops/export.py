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
xmrwallet.ops.export: Monero wallet ops for the MMGen Suite
"""

from ...util import gmsg, gmsg_r

from ..file.outputs import MoneroWalletOutputsFile
from ..rpc import MoneroWalletRPC

from .wallet import OpWallet

class OpExportOutputs(OpWallet):
	action = 'exporting outputs from'
	stem = 'process'
	sign = False

	async def process_wallet(self, d, fn, last):
		h = MoneroWalletRPC(self, d)
		h.open_wallet('source')

		if self.cfg.rescan_blockchain:
			gmsg_r('\n  Rescanning blockchain...')
			self.c.call('rescan_blockchain')
			gmsg('done')

		if self.cfg.rescan_spent:
			gmsg_r('\n  Rescanning spent outputs...')
			self.c.call('rescan_spent')
			gmsg('done')

		self.head_msg(d.idx, h.fn)
		for ftype in ('Unsigned', 'Signed'):
			old_fn = getattr(MoneroWalletOutputsFile, ftype).find_fn_from_wallet_fn(
				cfg             = self.cfg,
				wallet_fn       = fn,
				ret_on_no_match = True)
			if old_fn:
				old_fn.unlink()
		m = MoneroWalletOutputsFile.New(
			parent    = self,
			wallet_fn = fn,
			data      = self.c.call('export_outputs', all=True),
			sign      = self.sign,
		)
		m.write()
		return True

class OpExportOutputsSign(OpExportOutputs):
	opts = ('rescan_spent', 'rescan_blockchain')
	sign = True
