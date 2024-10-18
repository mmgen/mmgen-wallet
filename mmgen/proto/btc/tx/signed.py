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
proto.btc.tx.signed: Bitcoin signed transaction class
"""

from ....tx import signed as TxBase
from ....util import fmt, die
from .completed import Completed

class Signed(Completed, TxBase.Signed):

	def compare_size_and_estimated_size(self, tx_decoded):
		est_vsize = self.estimate_size()
		d = tx_decoded
		vsize = d['vsize'] if 'vsize' in d else d['size']
		self.cfg._util.vmsg(f'\nVsize: {vsize} (true) {est_vsize} (estimated)')
		ratio = float(est_vsize) / vsize
		if not (0.95 < ratio < 1.05): # allow for 5% error
			die('BadTxSizeEstimate', fmt(f"""
				Estimated transaction vsize is {ratio:1.2f} times the true vsize
				Your transaction fee estimates will be inaccurate
				Please re-create and re-sign the transaction using the option --vsize-adj={1/ratio:1.2f}
			""").strip())

class AutomountSigned(TxBase.AutomountSigned, Signed):
	pass
