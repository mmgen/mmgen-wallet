#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
proto.eth.tw.ctl: Ethereum tracking wallet control class
"""

from ....util import msg, ymsg, die, cached_property
from ....tw.store import TwCtlWithStore
from ....tw.ctl import write_mode
from ....addr import is_coin_addr

from ..contract import Token

class EthereumTwCtl(TwCtlWithStore):

	data_key = 'accounts'

	def init_empty(self):
		self.data = {
			'coin': self.proto.coin,
			'network': self.proto.network.upper(),
			'accounts': {},
			'tokens': {}}

	def upgrade_wallet_maybe(self):

		upgraded = False

		if not 'accounts' in self.data or not 'coin' in self.data:
			ymsg(f'Upgrading {self.desc} (v1->v2: accounts field added)')
			if not 'accounts' in self.data:
				self.data = {}
				import json
				self.data['accounts'] = json.loads(self.orig_data)
			if not 'coin' in self.data:
				self.data['coin'] = self.proto.coin
			upgraded = True

		def have_token_params_fields():
			for k in self.data['tokens']:
				if 'params' in self.data['tokens'][k]:
					return True

		def add_token_params_fields():
			for k in self.data['tokens']:
				self.data['tokens'][k]['params'] = {}

		if not 'tokens' in self.data:
			self.data['tokens'] = {}
			upgraded = True

		if self.data['tokens'] and not have_token_params_fields():
			ymsg(f'Upgrading {self.desc} (v2->v3: token params fields added)')
			add_token_params_fields()
			upgraded = True

		if not 'network' in self.data:
			ymsg(f'Upgrading {self.desc} (v3->v4: network field added)')
			self.data['network'] = self.proto.network.upper()
			upgraded = True

		if upgraded:
			self.force_write()
			msg(f'{self.desc} upgraded successfully!')

	async def rpc_get_balance(self, addr, block='latest'):
		return self.proto.coin_amt(
			int(await self.rpc.call('eth_getBalance', '0x' + addr, block), 16),
			from_unit = 'wei')

	async def addr2sym(self, req_addr):
		for addr in self.data['tokens']:
			if addr == req_addr:
				return self.data['tokens'][addr]['params']['symbol']

	async def sym2addr(self, sym):
		for addr in self.data['tokens']:
			if self.data['tokens'][addr]['params']['symbol'].upper() == sym.upper():
				return addr

	# Since it’s nearly impossible to empty an Ethereum account, consider set of used addresses
	# to be all accounts with balances.
	# Token addresses might have a balance but no corresponding ETH balance, so check them too.
	@cached_property
	def used_addrs(self):
		from decimal import Decimal
		return (
			{k for k, v in self.data['accounts'].items() if Decimal(v.get('balance', 0))} |
			{k for t in self.data['tokens'].values() for k, v in t.items()
				if Decimal(v.get('balance', 0))})

class EthereumTokenTwCtl(EthereumTwCtl):

	desc = 'Ethereum token tracking wallet'
	decimals = None
	symbol = None
	cur_eth_balances = {}

	async def __init__(self, cfg, proto, *, mode='r', token_addr=None, no_rpc=False):

		await super().__init__(cfg, proto, mode=mode, no_rpc=no_rpc)

		for v in self.data['tokens'].values():
			self.conv_types(v)

		if self.importing and token_addr:
			if not is_coin_addr(proto, token_addr):
				die('InvalidContractAddress', f'{token_addr!r}: invalid token address')
		else:
			assert token_addr is None, 'EthereumTokenTwCtl_chk1'
			token_addr = await self.sym2addr(proto.tokensym) # returns None on failure
			if not is_coin_addr(proto, token_addr):
				die('UnrecognizedTokenSymbol', f'Specified token {proto.tokensym!r} could not be resolved!')

		from ....addr import ContractAddr
		self.token = ContractAddr(proto, token_addr)

		if self.token not in self.data['tokens']:
			if self.importing:
				await self.import_token(self.token)
			else:
				die('TokenNotInWallet', f'Specified token {self.token!r} not in wallet!')

		self.decimals = self.get_param('decimals')
		self.symbol   = self.get_param('symbol')
		if mode == 'i' and not proto.tokensym:
			proto.tokensym = self.symbol

	@property
	def data_root(self):
		return self.data['tokens'][self.token]

	@property
	def data_root_desc(self):
		return 'token ' + self.get_param('symbol')

	async def rpc_get_balance(self, addr, block='latest'):
		return await Token(
			self.cfg,
			self.proto,
			self.token,
			decimals = self.decimals,
			rpc = self.rpc).get_balance(addr, block=block)

	async def get_eth_balance(self, addr, *, force_rpc=False, block='latest'):
		cache = self.cur_eth_balances
		r = self.data['accounts']
		ret = None if force_rpc else self.get_cached_balance(addr, cache, r)
		if ret is None:
			ret = await super().rpc_get_balance(addr, block=block)
			self.cache_balance(addr, ret, session_cache=cache, data_root=r)
		return ret

	def get_param(self, param):
		return self.data['tokens'][self.token]['params'][param]

	@write_mode
	async def import_token(self, tokenaddr):
		"""
		Token 'symbol' and 'decimals' values are resolved from the network by the system just
		once, upon token import.  Thereafter, token address, symbol and decimals are resolved
		either from the tracking wallet (online operations) or transaction file (when signing).
		"""
		t = Token(self.cfg, self.proto, tokenaddr, rpc=self.rpc)
		self.data['tokens'][tokenaddr] = {
			'params': {
				'symbol': await t.get_symbol(),
				'decimals': await t.get_decimals()}}
