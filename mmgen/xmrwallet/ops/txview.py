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
xmrwallet.ops.txview: Monero wallet ops for the MMGen Suite
"""

from pathlib import Path

from ...util import die

from ..file.tx import MoneroMMGenTX as mtx

from . import OpBase

class OpTxview(OpBase):
	view_method = 'get_info'
	opts = ('watch_only', 'autosign')
	hdr = ''
	col_hdr = ''
	footer = ''
	do_umount = False

	async def main(self, *, cols=None):

		self.mount_removable_device()

		if self.cfg.autosign:
			files = [f for f in getattr(self.asi, self.tx_dir).iterdir()
						if f.name.endswith('.' + mtx.Submitted.ext)]
		else:
			files = self.uargs.infile

		txs = sorted(
			(mtx.View(self.cfg, Path(fn)) for fn in files),
				# old TX files have no ‘submit_time’ field:
				key = lambda x: getattr(x.data, 'submit_time', None) or x.data.create_time)

		if self.cfg.autosign:
			self.asi.do_umount()

		addr_w = None if self.cfg.full_address or cols is None else cols - self.fixed_cols_w

		self.cfg._util.stdout_or_pager(
			(self.hdr if len(files) > 1 else '')
			+ self.col_hdr
			+ '\n'.join(getattr(tx, self.view_method)(addr_w=addr_w) for tx in txs)
			+ self.footer)

class OpTxlist(OpTxview):
	view_method = 'get_info_oneline'
	add_nl = True
	footer = '\n'
	fixed_cols_w = mtx.Base.oneline_fixed_cols_w
	min_addr_w = 10

	@property
	def hdr(self):
		return ('SUBMITTED ' if self.cfg.autosign else '') + 'MONERO TRANSACTIONS\n'

	@property
	def col_hdr(self):
		return mtx.View.oneline_fs.format(
			a = 'Network',
			b = 'Seed ID',
			c = 'Submitted' if self.cfg.autosign else 'Date',
			d = 'TxID',
			e = 'Type',
			f = 'Src',
			g = 'Dest',
			h = '  Amount',
			j = 'Dest Address',
			x = '',
		) + '\n'

	async def main(self):
		if self.cfg.pager:
			cols = None
		else:
			from ...term import get_terminal_size
			cols = self.cfg.columns or get_terminal_size().width
			if cols < self.fixed_cols_w + self.min_addr_w:
				die(1, f'A terminal at least {self.fixed_cols_w + self.min_addr_w} columns wide is'
						' required to display this output (or use --columns or --pager)')
		await super().main(cols=cols)
