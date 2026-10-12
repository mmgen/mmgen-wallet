# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
tx.base_swap: base swap transaction mixin class
"""

from ..util import die, cached_property

class BaseSwapMethods:
	data_desc = 'swap transaction data'

	@property
	def vault_idx(self):
		return self._chg_output_ops('idx', 'is_vault')

	@property
	def vault_output(self):
		return self._chg_output_ops('output', 'is_vault')

	@cached_property
	def swap_proto_rpc(self):
		from ..swap.util import get_swap_proto_rpc
		return get_swap_proto_rpc(self.cfg, self.swap_proto_mod.coin)

	@cached_property
	def swap_proto_mod(self):
		from ..swap.util import get_swap_proto_mod
		return get_swap_proto_mod(self.swap_proto)

	@cached_property
	def send_asset(self):
		spec = self.proto.coin + (f'.{self.proto.tokensym}' if self.proto.tokensym else '')
		return self.swap_proto_mod.SwapAsset(spec, 'send')

	@cached_property
	def recv_asset(self):
		if hasattr(self, 'swap_recv_asset_spec'):
			return self.swap_proto_mod.SwapAsset(self.swap_recv_asset_spec, 'recv')
		elif self.is_swap and hasattr(self, 'data_output'):
			from ..swap.proto.thorchain.memo import THORChainMemo
			return THORChainMemo.parse(str(self.data_output.data)).asset
		else: # backwards-compatibility workaround
			from ..swap.asset import SwapAsset
			x = '[unknown]'
			return SwapAsset._ad(x, x, x, x, x, x)

	def check_swap_network(self):
		rpc = self.swap_proto_rpc
		data = rpc.inbound_addrs()
		for asset in (self.send_asset, self.recv_asset):
			if asset.name != 'RUNE':
				for key, state in (
						('global_trading_paused', 'paused'),
						('chain_trading_paused',  f'paused for asset {asset.name}'),
						('halted',                f'halted for asset {asset.name}')):
					if rpc.data_for_coin(data, asset.coin)[key]:
						die(2, f'Trading is {state} on the {self.swap_proto_mod.name} network')
