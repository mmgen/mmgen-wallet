#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
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

from mmgen.common import *
from mmgen.obj import ETHAmt,TwLabel,is_coin_addr,is_mmgen_id,MMGenListItem,ListItemAttr,ImmutableAttr
from mmgen.tw import TrackingWallet,TwAddrList,TwUnspentOutputs
from mmgen.addr import AddrData
from .contract import Token

class EthereumTrackingWallet(TrackingWallet):

	caps = ()
	data_key = 'accounts'
	use_tw_file = True

	def __init__(self,mode='r',no_rpc=False):
		TrackingWallet.__init__(self,mode=mode)

		for v in self.data['tokens'].values():
			self.conv_types(v)

		if g.token and not is_coin_addr(g.token):
			ret = self.sym2addr(g.token,no_rpc=no_rpc)
			if ret: g.token = ret

	def is_in_wallet(self,addr):
		return addr in self.data_root

	def init_empty(self):
		self.data = { 'coin': g.coin, 'accounts': {}, 'tokens': {} }

	def upgrade_wallet_maybe(self):

		upgraded = False

		if not 'accounts' in self.data or not 'coin' in self.data:
			ymsg('Upgrading {} (v1->v2: accounts field added)'.format(self.desc))
			if not 'accounts' in self.data:
				self.data = {}
				import json
				self.data['accounts'] = json.loads(self.orig_data)
			if not 'coin' in self.data:
				self.data['coin'] = g.coin
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
			ymsg('Upgrading {} (v2->v3: token params fields added)'.format(self.desc))
			add_token_params_fields()
			upgraded = True

		if upgraded:
			self.force_write()
			msg('{} upgraded successfully!'.format(self.desc))

	# Don't call rpc_init() for Ethereum, because it may create a wallet instance
	def rpc_init(self): pass

	def rpc_get_balance(self,addr):
		return ETHAmt(int(g.rpch.eth_getBalance('0x'+addr),16),'wei')

	@write_mode
	def import_address(self,addr,label,foo):
		r = self.data_root
		if addr in r:
			if not r[addr]['mmid'] and label.mmid:
				msg(f'Warning: MMGen ID {label.mmid!r} was missing in tracking wallet!')
			elif r[addr]['mmid'] != label.mmid:
				die(3,'MMGen ID {label.mmid!r} does not match tracking wallet!')
		r[addr] = { 'mmid': label.mmid, 'comment': label.comment }

	@write_mode
	def remove_address(self,addr):
		r = self.data_root

		if is_coin_addr(addr):
			have_match = lambda k: k == addr
		elif is_mmgen_id(addr):
			have_match = lambda k: r[k]['mmid'] == addr
		else:
			die(1,"'{}' is not an Ethereum address or MMGen ID".format(addr))

		for k in r:
			if have_match(k):
				# return the addr resolved to mmid if possible
				ret = r[k]['mmid'] if is_mmgen_id(r[k]['mmid']) else addr
				del r[k]
				self.write()
				return ret
		else:
			m = "Address '{}' not found in '{}' section of tracking wallet"
			msg(m.format(addr,self.data_root_desc))
			return None

	@write_mode
	def set_label(self,coinaddr,lbl):
		for addr,d in list(self.data_root.items()):
			if addr == coinaddr:
				d['comment'] = lbl.comment
				self.write()
				return None
		else: # emulate on_fail='return' of RPC library
			m = "Address '{}' not found in '{}' section of tracking wallet"
			return ('rpcfail',(None,2,m.format(coinaddr,self.data_root_desc)))

	def addr2sym(self,req_addr):

		for addr in self.data['tokens']:
			if addr == req_addr:
				ret = self.data['tokens'][addr]['params'].get('symbol')
				if ret: return ret
				else: break

		self.token_obj = Token(req_addr)
		ret = self.token_obj.symbol().upper()
		self.force_set_token_param(req_addr,'symbol',ret)
		return ret

	def sym2addr(self,sym,no_rpc=False):

		for addr in self.data['tokens']:
			if self.data['tokens'][addr]['params'].get('symbol') == sym.upper():
				return addr

		if no_rpc:
			return None

		for addr in self.data['tokens']:
			if Token(addr).symbol().upper() == sym.upper():
				self.force_set_token_param(addr,'symbol',sym.upper())
				return addr
		else:
			return None

	def get_token_param(self,token,param):
		if token in self.data['tokens']:
			return self.data['tokens'][token]['params'].get(param)
		return None

	def force_set_token_param(self,*args,**kwargs):
		mode_save = self.mode
		self.mode = 'w'
		self.set_token_param(*args,**kwargs)
		self.mode = mode_save

	@write_mode
	def set_token_param(self,token,param,val):
		if token in self.data['tokens']:
			self.data['tokens'][token]['params'][param] = val

class EthereumTokenTrackingWallet(EthereumTrackingWallet):

	desc = 'Ethereum token tracking wallet'
	decimals = None
	symbol = None
	cur_eth_balances = {}

	def __init__(self,mode='r',no_rpc=False):
		EthereumTrackingWallet.__init__(self,mode=mode,no_rpc=no_rpc)

		self.desc = 'Ethereum token tracking wallet'

		if not is_coin_addr(g.token):
			raise UnrecognizedTokenSymbol('Specified token {!r} could not be resolved!'.format(g.token))

		if mode == 'r' and not g.token in self.data['tokens']:
			raise TokenNotInWallet('Specified token {!r} not in wallet!'.format(g.token))

		self.token = g.token

		if self.token in self.data['tokens']:
			for k in ('decimals','symbol'):
				setattr(self,k,self.get_param(k))
				if getattr(self,k) == None:
					setattr(self,k,getattr(Token(self.token,self.decimals),k)())
					if getattr(self,k) != None:
						self.set_param(k,getattr(self,k))
						self.write()

	def is_in_wallet(self,addr):
		return addr in self.data['tokens'][self.token]

	@property
	def data_root(self):
		return self.data['tokens'][self.token]

	@property
	def data_root_desc(self):
		return 'token ' + Token(self.token,self.decimals).symbol()

	@write_mode
	def add_token(self,token):
		msg("Adding token '{}' to tracking wallet.".format(token))
		self.data['tokens'][token] = { 'params': {} }

	@write_mode
	def import_address(self,*args,**kwargs):
		if self.token not in self.data['tokens']:
			self.add_token(self.token)
		EthereumTrackingWallet.import_address(self,*args,**kwargs)

	def rpc_get_balance(self,addr):
		return Token(self.token,self.decimals).balance(addr)

	def get_eth_balance(self,addr,force_rpc=False):
		cache = self.cur_eth_balances
		data_root = self.data['accounts']
		ret = None if force_rpc else self.get_cached_balance(addr,cache,data_root)
		if ret == None:
			ret = EthereumTrackingWallet.rpc_get_balance(self,addr)
			self.cache_balance(addr,ret,cache,data_root)
		return ret

	def force_set_param(self,*args,**kwargs):
		mode_save = self.mode
		self.mode = 'w'
		self.set_param(*args,**kwargs)
		self.mode = mode_save

	@write_mode
	def set_param(self,param,val):
		self.data['tokens'][self.token]['params'][param] = val

	def get_param(self,param):
		return self.data['tokens'][self.token]['params'].get(param)

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

	def __init__(self,*args,**kwargs):
		if g.use_cached_balances:
			self.hdr_fmt += '\n' + yellow('WARNING: Using cached balances. These may be out of date!')
		TwUnspentOutputs.__init__(self,*args,**kwargs)

	def do_sort(self,key=None,reverse=False):
		if key == 'txid': return
		super().do_sort(key=key,reverse=reverse)

	def get_unspent_rpc(self):
		wl = self.wallet.sorted_list
		if self.addrs:
			wl = [d for d in wl if d['addr'] in self.addrs]
		return [{
				'account': TwLabel(d['mmid']+' '+d['comment'],on_fail='raise'),
				'address': d['addr'],
				'amount': self.wallet.get_balance(d['addr']),
				'confirmations': 0, # TODO
				} for d in wl]

	class MMGenTwUnspentOutput(MMGenListItem):
		txid   = ListItemAttr('CoinTxID')
		vout   = ListItemAttr(int,typeconv=False)
		amt    = ImmutableAttr(lambda:g.proto.coin_amt,typeconv=False)
		amt2   = ListItemAttr(lambda:g.proto.coin_amt,typeconv=False)
		label  = ListItemAttr('TwComment',reassign_ok=True)
		twmmid = ImmutableAttr('TwMMGenID')
		addr   = ImmutableAttr('CoinAddr')
		confs  = ImmutableAttr(int,typeconv=False)
		skip   = ListItemAttr(str,typeconv=False,reassign_ok=True)

	def age_disp(self,o,age_fmt): # TODO
		return None

class EthereumTokenTwUnspentOutputs(EthereumTwUnspentOutputs):

	disp_type = 'token'
	prompt_fs = 'Total to spend: {} {}\n\n'
	col_adj = 37

	def get_display_precision(self):
		return 10 # truncate precision for narrow display

	def get_unspent_data(self):
		super().get_unspent_data()
		for e in self.unspent:
			e.amt2 = self.wallet.get_eth_balance(e.addr)

class EthereumTwAddrList(TwAddrList):

	has_age = False

	def __init__(self,usr_addr_list,minconf,showempty,showbtcaddrs,all_labels,wallet=None):

		self.wallet = wallet or TrackingWallet(mode='w')
		tw_dict = self.wallet.mmid_ordered_dict
		self.total = g.proto.coin_amt('0')

		from mmgen.obj import CoinAddr
		for mmid,d in list(tw_dict.items()):
#			if d['confirmations'] < minconf: continue # cannot get confirmations for eth account
			label = TwLabel(mmid+' '+d['comment'],on_fail='raise')
			if usr_addr_list and (label.mmid not in usr_addr_list):
				continue
			bal = self.wallet.get_balance(d['addr'])
			if bal == 0 and not showempty:
				if not label.comment or not all_labels:
					continue
			self[label.mmid] = {'amt': g.proto.coin_amt('0'), 'lbl':  label }
			if showbtcaddrs:
				self[label.mmid]['addr'] = CoinAddr(d['addr'])
			self[label.mmid]['lbl'].mmid.confs = None
			self[label.mmid]['amt'] += bal
			self.total += bal

class EthereumTokenTwAddrList(EthereumTwAddrList): pass

from mmgen.tw import TwGetBalance
class EthereumTwGetBalance(TwGetBalance):

	fs = '{w:13} {c}\n' # TODO - for now, just suppress display of meaningless data

	def __init__(self,*args,**kwargs):
		self.wallet = TrackingWallet(mode='w')
		TwGetBalance.__init__(self,*args,**kwargs)

	def create_data(self):
		data = self.wallet.mmid_ordered_dict
		for d in data:
			if d.type == 'mmgen':
				key = d.obj.sid
				if key not in self.data:
					self.data[key] = [g.proto.coin_amt('0')] * 4
			else:
				key = 'Non-MMGen'

			conf_level = 2 # TODO
			amt = self.wallet.get_balance(data[d]['addr'])

			self.data['TOTAL'][conf_level] += amt
			self.data[key][conf_level] += amt

class EthereumTokenTwGetBalance(EthereumTwGetBalance): pass

class EthereumAddrData(AddrData):

	@classmethod
	def get_tw_data(cls,wallet=None):
		vmsg('Getting address data from tracking wallet')
		tw = (wallet or TrackingWallet()).mmid_ordered_dict
		# emulate the output of RPC 'listaccounts' and 'getaddressesbyaccount'
		return [(mmid+' '+d['comment'],[d['addr']]) for mmid,d in list(tw.items())]

class EthereumTokenAddrData(EthereumAddrData): pass
