# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
swap.proto.thorchain.memoless: THORChain swap protocol memoless classes for the MMGen Wallet suite
"""

from ....amt import CoinAmt, TokenAmt

class THORChainReferenceMemo:

	pfx = 'REFERENCE'

	def __init__(self, send_asset=None, memo=None, reference_memo_str=None):
		if reference_memo_str is None:
			assert send_asset and memo, 'THORChainReferenceMemo_err1'
			self.send_asset = send_asset
			self.memo = memo
		else:
			assert send_asset is memo is None, 'THORChainReferenceMemo_err2'
			self.parse(reference_memo_str)

	def __str__(self):
		return f'{self.pfx}:{self.send_asset.full_name}:{self.memo}'

	def parse(self, s):
		from .asset import THORChainSwapAsset
		pfx, name, self.memo = s.split(':', 2)
		assert pfx.upper() == self.pfx, f'{pfx}: invalid reference memo prefix'
		self.send_asset = THORChainSwapAsset(name, 'send', sanitize_input=True)

class THORChainMemolessAmount:

	mod = 100000

	def __init__(self, amt, refnum=None, *, round_down=False):
		assert isinstance(amt, CoinAmt), 'amount must be CoinAmt instance'
		if refnum:
			adj = lambda diff: diff - (
				(self.mod if diff > 0 else 0) if round_down else
				(0 if abs(diff) <= self.mod // 2 else self.mod if diff > 0 else -self.mod))
			from ....util import is_int
			assert is_int(refnum) and refnum < self.mod, f'refnum must be an integer < {self.mod}'
			orig_amt = amt.to_unit('atomic')
			self.int_amt = orig_amt + adj(refnum - orig_amt % self.mod)
			self.amt = type(amt)(
				self.int_amt,
				from_unit = 'atomic',
				decimals = amt.max_prec if isinstance(amt, TokenAmt) else None)
			self.refnum = refnum
		else:
			self.int_amt = amt.to_unit('atomic')
			self.amt = amt
			self.refnum = self.int_amt % self.mod
