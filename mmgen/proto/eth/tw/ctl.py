#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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

from ....util import msg, ymsg, die
from ....tw.ctl import TwCtl, write_mode, label_addr_pair
from ....tw.shared import TwLabel
from ....addr import is_coin_addr, is_mmgen_id, CoinAddr
from ..contract import Token, ResolvedToken

class EthereumTwCtl(TwCtl):

	caps = ('batch',)
	data_key = 'accounts'
	use_tw_file = True

	def init_empty(self):
		self.data = {
			'coin': self.proto.coin,
			'network': self.proto.network.upper(),
			'accounts': {},
			'tokens': {},
		}

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

	async def rpc_get_balance(self, addr):
		return self.proto.coin_amt(
			int(await self.rpc.call('eth_getBalance', '0x' + addr, 'latest'), 16),
			from_unit = 'wei')

	@write_mode
	async def batch_import_address(self, args_list):
		return [await self.import_address(*a) for a in args_list]

	async def rescan_addresses(self, coin_addrs):
		pass

	@write_mode
	async def import_address(self, addr, label, rescan=False):
		r = self.data_root
		if addr in r:
			if not r[addr]['mmid'] and label.mmid:
				msg(f'Warning: MMGen ID {label.mmid!r} was missing in tracking wallet!')
			elif r[addr]['mmid'] != label.mmid:
				die(3, 'MMGen ID {label.mmid!r} does not match tracking wallet!')
		r[addr] = {'mmid': label.mmid, 'comment': label.comment}

	@write_mode
	async def remove_address(self, addr):
		r = self.data_root

		if is_coin_addr(self.proto, addr):
			have_match = lambda k: k == addr
		elif is_mmgen_id(self.proto, addr):
			have_match = lambda k: r[k]['mmid'] == addr
		else:
			die(1, f'{addr!r} is not an Ethereum address or MMGen ID')

		for k in r:
			if have_match(k):
				# return the addr resolved to mmid if possible
				ret = r[k]['mmid'] if is_mmgen_id(self.proto, r[k]['mmid']) else addr
				del r[k]
				self.write()
				return ret
		msg(f'Address {addr!r} not found in {self.data_root_desc!r} section of tracking wallet')
		return None

	@write_mode
	async def set_label(self, coinaddr, lbl):
		for addr, d in list(self.data_root.items()):
			if addr == coinaddr:
				d['comment'] = lbl.comment
				self.write()
				return True
		msg(f'Address {coinaddr!r} not found in {self.data_root_desc!r} section of tracking wallet')
		return False

	async def addr2sym(self, req_addr):
		for addr in self.data['tokens']:
			if addr == req_addr:
				return self.data['tokens'][addr]['params']['symbol']

	async def sym2addr(self, sym):
		for addr in self.data['tokens']:
			if self.data['tokens'][addr]['params']['symbol'] == sym.upper():
				return addr

	def get_token_param(self, token, param):
		if token in self.data['tokens']:
			return self.data['tokens'][token]['params'].get(param)

	@property
	def sorted_list(self):
		return sorted([{
				'addr':    x[0],
				'mmid':    x[1]['mmid'],
				'comment': x[1]['comment']
			} for x in self.data_root.items() if x[0] not in ('params', 'coin')],
			key = lambda x: x['mmid'].sort_key + x['addr'])

	@property
	def mmid_ordered_dict(self):
		return dict((x['mmid'], {'addr': x['addr'], 'comment': x['comment']}) for x in self.sorted_list)

	async def get_label_addr_pairs(self):
		return [label_addr_pair(
				TwLabel(self.proto, f"{mmid} {d['comment']}"),
				CoinAddr(self.proto, d['addr'])
			) for mmid, d in self.mmid_ordered_dict.items()]

class EthereumTokenTwCtl(EthereumTwCtl):

	desc = 'Ethereum token tracking wallet'
	decimals = None
	symbol = None
	cur_eth_balances = {}

	async def __init__(self, cfg, proto, mode='r', token_addr=None, no_rpc=False):

		await super().__init__(cfg, proto, mode=mode, no_rpc=no_rpc)

		for v in self.data['tokens'].values():
			self.conv_types(v)

		if self.importing and token_addr:
			if not is_coin_addr(proto, token_addr):
				die('InvalidTokenAddress', f'{token_addr!r}: invalid token address')
		else:
			assert token_addr is None, 'EthereumTokenTwCtl_chk1'
			token_addr = await self.sym2addr(proto.tokensym) # returns None on failure
			if not is_coin_addr(proto, token_addr):
				die('UnrecognizedTokenSymbol', f'Specified token {proto.tokensym!r} could not be resolved!')

		from ....addr import TokenAddr
		self.token = TokenAddr(proto, token_addr)

		if self.token not in self.data['tokens']:
			if self.importing:
				await self.import_token(self.token)
			else:
				die('TokenNotInWallet', f'Specified token {self.token!r} not in wallet!')

		self.decimals = self.get_param('decimals')
		self.symbol   = self.get_param('symbol')

		proto.tokensym = self.symbol

	@property
	def data_root(self):
		return self.data['tokens'][self.token]

	@property
	def data_root_desc(self):
		return 'token ' + self.get_param('symbol')

	async def rpc_get_balance(self, addr):
		return await Token(self.cfg, self.proto, self.token, self.decimals, self.rpc).get_balance(addr)

	async def get_eth_balance(self, addr, force_rpc=False):
		cache = self.cur_eth_balances
		r = self.data['accounts']
		ret = None if force_rpc else self.get_cached_balance(addr, cache, r)
		if ret is None:
			ret = await super().rpc_get_balance(addr)
			self.cache_balance(addr, ret, cache, r)
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
		t = await ResolvedToken(self.cfg, self.proto, self.rpc, tokenaddr)
		self.data['tokens'][tokenaddr] = {
			'params': {
				'symbol': await t.get_symbol(),
				'decimals': t.decimals
			}
		}
