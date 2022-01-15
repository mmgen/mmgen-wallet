#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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
altcoins.eth.tw: Ethereum tracking wallet and related classes for the MMGen suite
"""

import os

from mmgen.util import msg,vmsg,ymsg,write_mode
from mmgen.obj import ListItemAttr,ImmutableAttr
from mmgen.tw import TrackingWallet,TwAddrList,TwUnspentOutputs,TwGetBalance,TwLabel
from mmgen.addr import is_coin_addr,is_mmgen_id
from mmgen.addrdata import AddrData,TwAddrData
from .contract import Token,TokenResolve
from .obj import ETHAmt

class EthereumTrackingWallet(TrackingWallet):

	caps = ('batch',)
	data_key = 'accounts'
	use_tw_file = True

	async def is_in_wallet(self,addr):
		return addr in self.data_root

	def init_empty(self):
		self.data = { 'coin': self.proto.coin, 'accounts': {}, 'tokens': {} }

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

		if upgraded:
			self.force_write()
			msg(f'{self.desc} upgraded successfully!')

	async def rpc_get_balance(self,addr):
		return ETHAmt(int(await self.rpc.call('eth_getBalance','0x'+addr,'latest'),16),'wei')

	@write_mode
	async def batch_import_address(self,args_list):
		for arg_list in args_list:
			await self.import_address(*arg_list)
		return args_list

	@write_mode
	async def import_address(self,addr,label,foo):
		r = self.data_root
		if addr in r:
			if not r[addr]['mmid'] and label.mmid:
				msg(f'Warning: MMGen ID {label.mmid!r} was missing in tracking wallet!')
			elif r[addr]['mmid'] != label.mmid:
				die(3,'MMGen ID {label.mmid!r} does not match tracking wallet!')
		r[addr] = { 'mmid': label.mmid, 'comment': label.comment }

	@write_mode
	async def remove_address(self,addr):
		r = self.data_root

		if is_coin_addr(self.proto,addr):
			have_match = lambda k: k == addr
		elif is_mmgen_id(self.proto,addr):
			have_match = lambda k: r[k]['mmid'] == addr
		else:
			die(1,f'{addr!r} is not an Ethereum address or MMGen ID')

		for k in r:
			if have_match(k):
				# return the addr resolved to mmid if possible
				ret = r[k]['mmid'] if is_mmgen_id(self.proto,r[k]['mmid']) else addr
				del r[k]
				self.write()
				return ret
		else:
			msg(f'Address {addr!r} not found in {self.data_root_desc!r} section of tracking wallet')
			return None

	@write_mode
	async def set_label(self,coinaddr,lbl):
		for addr,d in list(self.data_root.items()):
			if addr == coinaddr:
				d['comment'] = lbl.comment
				self.write()
				return None
		else:
			msg(f'Address {coinaddr!r} not found in {self.data_root_desc!r} section of tracking wallet')
			return False

	async def addr2sym(self,req_addr):
		for addr in self.data['tokens']:
			if addr == req_addr:
				return self.data['tokens'][addr]['params']['symbol']
		else:
			return None

	async def sym2addr(self,sym):
		for addr in self.data['tokens']:
			if self.data['tokens'][addr]['params']['symbol'] == sym.upper():
				return addr
		else:
			return None

	def get_token_param(self,token,param):
		if token in self.data['tokens']:
			return self.data['tokens'][token]['params'].get(param)
		return None

class EthereumTokenTrackingWallet(EthereumTrackingWallet):

	desc = 'Ethereum token tracking wallet'
	decimals = None
	symbol = None
	cur_eth_balances = {}

	async def __init__(self,proto,mode='r',token_addr=None):
		await super().__init__(proto,mode=mode)

		for v in self.data['tokens'].values():
			self.conv_types(v)

		if self.importing and token_addr:
			if not is_coin_addr(proto,token_addr):
				raise InvalidTokenAddress(f'{token_addr!r}: invalid token address')
		else:
			assert token_addr == None,'EthereumTokenTrackingWallet_chk1'
			token_addr = await self.sym2addr(proto.tokensym) # returns None on failure
			if not is_coin_addr(proto,token_addr):
				from mmgen.exception import UnrecognizedTokenSymbol
				raise UnrecognizedTokenSymbol(f'Specified token {proto.tokensym!r} could not be resolved!')

		from mmgen.addr import TokenAddr
		self.token = TokenAddr(proto,token_addr)

		if self.token not in self.data['tokens']:
			if self.importing:
				await self.import_token(self.token)
			else:
				raise TokenNotInWallet(f'Specified token {self.token!r} not in wallet!')

		self.decimals = self.get_param('decimals')
		self.symbol   = self.get_param('symbol')

		proto.tokensym = self.symbol

	async def is_in_wallet(self,addr):
		return addr in self.data['tokens'][self.token]

	@property
	def data_root(self):
		return self.data['tokens'][self.token]

	@property
	def data_root_desc(self):
		return 'token ' + self.get_param('symbol')

	async def rpc_get_balance(self,addr):
		return await Token(self.proto,self.token,self.decimals,self.rpc).get_balance(addr)

	async def get_eth_balance(self,addr,force_rpc=False):
		cache = self.cur_eth_balances
		r = self.data['accounts']
		ret = None if force_rpc else self.get_cached_balance(addr,cache,r)
		if ret == None:
			ret = await super().rpc_get_balance(addr)
			self.cache_balance(addr,ret,cache,r)
		return ret

	def get_param(self,param):
		return self.data['tokens'][self.token]['params'][param]

	@write_mode
	async def import_token(self,tokenaddr):
		"""
		Token 'symbol' and 'decimals' values are resolved from the network by the system just
		once, upon token import.  Thereafter, token address, symbol and decimals are resolved
		either from the tracking wallet (online operations) or transaction file (when signing).
		"""
		t = await TokenResolve(self.proto,self.rpc,tokenaddr)
		self.data['tokens'][tokenaddr] = {
			'params': {
				'symbol': await t.get_symbol(),
				'decimals': t.decimals
			}
		}

# No unspent outputs with Ethereum, but naming must be consistent
class EthereumTwUnspentOutputs(TwUnspentOutputs):

	disp_type = 'eth'
	can_group = False
	col_adj = 29
	hdr_fmt = 'TRACKED ACCOUNTS (sort order: {})\nTotal {}: {}'
	desc    = 'account balances'
	item_desc = 'account'
	dump_fn_pfx = 'balances'
	prompt = """
Sort options:    [a]mount, a[d]dress, [r]everse, [M]mgen addr
Display options: show [m]mgen addr, r[e]draw screen
Actions:         [q]uit view, [p]rint to file, pager [v]iew, [w]ide view,
                 add [l]abel, [D]elete address, [R]efresh balance:
"""
	key_mappings = {
		'a':'s_amt','d':'s_addr','r':'d_reverse','M':'s_twmmid',
		'm':'d_mmid','e':'d_redraw',
		'q':'a_quit','p':'a_print','v':'a_view','w':'a_view_wide',
		'l':'a_lbl_add','D':'a_addr_delete','R':'a_balance_refresh' }

	async def __init__(self,proto,*args,**kwargs):
		from mmgen.globalvars import g
		if g.cached_balances:
			from mmgen.color import yellow
			self.hdr_fmt += '\n' + yellow('WARNING: Using cached balances. These may be out of date!')
		await TwUnspentOutputs.__init__(self,proto,*args,**kwargs)

	def do_sort(self,key=None,reverse=False):
		if key == 'txid': return
		super().do_sort(key=key,reverse=reverse)

	async def get_unspent_rpc(self):
		wl = self.wallet.sorted_list
		if self.addrs:
			wl = [d for d in wl if d['addr'] in self.addrs]
		return [{
				'account': TwLabel(self.proto,d['mmid']+' '+d['comment']),
				'address': d['addr'],
				'amount': await self.wallet.get_balance(d['addr']),
				'confirmations': 0, # TODO
				} for d in wl]

	class MMGenTwUnspentOutput(TwUnspentOutputs.MMGenTwUnspentOutput):
		valid_attrs = {'txid','vout','amt','amt2','label','twmmid','addr','confs','skip'}
		invalid_attrs = {'proto'}

	def age_disp(self,o,age_fmt): # TODO
		return None

class EthereumTokenTwUnspentOutputs(EthereumTwUnspentOutputs):

	disp_type = 'token'
	prompt_fs = 'Total to spend: {} {}\n\n'
	col_adj = 37

	def get_display_precision(self):
		return 10 # truncate precision for narrow display

	async def get_unspent_data(self,*args,**kwargs):
		await super().get_unspent_data(*args,**kwargs)
		for e in self.unspent:
			e.amt2 = await self.wallet.get_eth_balance(e.addr)

class EthereumTwAddrList(TwAddrList):

	has_age = False

	async def __init__(self,proto,usr_addr_list,minconf,showempty,showbtcaddrs,all_labels,wallet=None):

		self.proto = proto
		self.wallet = wallet or await TrackingWallet(self.proto,mode='w')
		tw_dict = self.wallet.mmid_ordered_dict
		self.total = self.proto.coin_amt('0')

		from mmgen.addr import CoinAddr
		for mmid,d in list(tw_dict.items()):
#			if d['confirmations'] < minconf: continue # cannot get confirmations for eth account
			label = TwLabel(self.proto,mmid+' '+d['comment'])
			if usr_addr_list and (label.mmid not in usr_addr_list):
				continue
			bal = await self.wallet.get_balance(d['addr'])
			if bal == 0 and not showempty:
				if not label.comment or not all_labels:
					continue
			self[label.mmid] = {'amt': self.proto.coin_amt('0'), 'lbl':  label }
			if showbtcaddrs:
				self[label.mmid]['addr'] = CoinAddr(self.proto,d['addr'])
			self[label.mmid]['lbl'].mmid.confs = None
			self[label.mmid]['amt'] += bal
			self.total += bal

		del self.wallet

class EthereumTokenTwAddrList(EthereumTwAddrList):
	pass

class EthereumTwGetBalance(TwGetBalance):

	fs = '{w:13} {c}\n' # TODO - for now, just suppress display of meaningless data

	async def __init__(self,proto,*args,**kwargs):
		self.wallet = await TrackingWallet(proto,mode='w')
		await TwGetBalance.__init__(self,proto,*args,**kwargs)

	async def create_data(self):
		data = self.wallet.mmid_ordered_dict
		for d in data:
			if d.type == 'mmgen':
				key = d.obj.sid
				if key not in self.data:
					self.data[key] = [self.proto.coin_amt('0')] * 4
			else:
				key = 'Non-MMGen'

			conf_level = 2 # TODO
			amt = await self.wallet.get_balance(data[d]['addr'])

			self.data['TOTAL'][conf_level] += amt
			self.data[key][conf_level] += amt

		del self.wallet

class EthereumTwAddrData(TwAddrData):

	async def get_tw_data(self,wallet=None):
		vmsg('Getting address data from tracking wallet')
		tw = (wallet or await TrackingWallet(self.proto)).mmid_ordered_dict
		# emulate the output of RPC 'listaccounts' and 'getaddressesbyaccount'
		return [(mmid+' '+d['comment'],[d['addr']]) for mmid,d in list(tw.items())]

class EthereumTokenTwGetBalance(EthereumTwGetBalance): pass
class EthereumTokenTwAddrData(EthereumTwAddrData): pass

class EthereumAddrData(AddrData): pass
class EthereumTokenAddrData(EthereumAddrData): pass
