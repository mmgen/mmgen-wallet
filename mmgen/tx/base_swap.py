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

from ..util import ymsg, die, cached_property
from ..addr import CoinAddr

class BaseSwapMethods:

	memoless_memo = None

	@property
	def data_desc(self):
		def gen():
			if self.is_memoless:
				yield 'memoless'
			yield 'swap'
			if self.is_refreq:
				yield 'reference request'
			yield 'transaction data'
		return ' '.join(gen())

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
		spec = getattr(
			self,
			'swap_send_asset_spec',
			self.proto.coin + (f'.{self.proto.tokensym}' if self.proto.tokensym else ''))
		return self.swap_proto_mod.SwapAsset(spec, 'send')

	@cached_property
	def recv_asset(self):
		if hasattr(self, 'swap_recv_asset_spec'):
			return self.swap_proto_mod.SwapAsset(self.swap_recv_asset_spec, 'recv')
		elif self.is_swap and hasattr(self, 'data_output'):
			return self.swap_proto_mod.Memo.parse(str(self.data_output.data)).asset
		else: # backwards-compatibility workaround
			from ..swap.asset import SwapAsset
			x = '[unknown]'
			return SwapAsset._ad(x, x, x, x, x, x)

	def check_swap_network(self):
		rpc = self.swap_proto_rpc
		if self.is_memoless:
			if not self.cfg.test_suite:
				die(2, 'Memoless swaps are currently disabled for mainnet in MMGen Wallet')
			self.mimir_data = rpc.mimir()
			fs = f'Memoless swaps are {{}} on the {self.swap_proto_mod.name} network'
			if self.mimir_data['HALTMEMOLESS']:
				die(2, fs.format('halted'))

		data = rpc.inbound_addrs()
		for asset in (self.send_asset, self.recv_asset):
			if asset.name != 'RUNE':
				for key, state in (
						('global_trading_paused', 'paused'),
						('chain_trading_paused',  f'paused for asset {asset.name}'),
						('halted',                f'halted for asset {asset.name}')):
					if rpc.data_for_coin(data, asset.coin)[key]:
						die(2, f'Trading is {state} on the {self.swap_proto_mod.name} network')

	async def parse_network_memo(self, *, data, recv_asset_spec, recv_twmmid, chk_only=False):
		from ..swap.util import init_swap_proto
		from ..tw.ctl import TwCtl
		pm = self.swap_proto_mod.Memo.parse(data['memo'])
		if pm.asset.name != recv_asset_spec:
			die(2,
				f'receive protocol mismatch: {pm.asset.name!r} (registered memo) '
				f'!= {recv_asset_spec!r} (cmdline)')
		pm_proto = init_swap_proto(self.cfg, pm.asset)
		ra = await (await TwCtl(self.cfg, pm_proto, mode='w')).resolve_address(pm.address)
		assert ra, f'unable to resolve address from registered memo {pm.address!r}'
		if recv_twmmid and recv_twmmid != ra.twmmid:
			ymsg(
				f'Warning: address from registered memo ({ra.twmmid!r}) '
				f'does not match our destination address ({recv_twmmid!r})')
		return None if chk_only else (
			self._output(pm.asset.coin, self.cfg.network, CoinAddr(pm_proto, pm.address), ra.twmmid),
			pm)
