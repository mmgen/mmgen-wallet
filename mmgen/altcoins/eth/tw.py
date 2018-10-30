#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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

import json
from mmgen.common import *
from mmgen.obj import ETHAmt,TwMMGenID,TwComment,TwLabel
from mmgen.tw import TrackingWallet,TwAddrList,TwUnspentOutputs
from mmgen.addr import AddrData
from mmgen.altcoins.eth.contract import Token

class EthereumTrackingWallet(TrackingWallet):

	desc = 'Ethereum tracking wallet'
	caps = ()

	data_dir = os.path.join(g.altcoin_data_dir,g.coin.lower(),g.proto.data_subdir)
	tw_file = os.path.join(data_dir,'tracking-wallet.json')

	def __init__(self,mode='r'):
		TrackingWallet.__init__(self,mode=mode)
		check_or_create_dir(self.data_dir)
		try:
			self.orig_data = get_data_from_file(self.tw_file,silent=True)
			self.data = json.loads(self.orig_data)
		except:
			try: os.stat(self.tw_file)
			except:
				self.orig_data = ''
				self.data = {'coin':g.coin,'accounts':{},'tokens':{}}
			else: die(2,"File '{}' exists but does not contain valid json data")
		else:
			self.upgrade_wallet_maybe()
			m = 'Tracking wallet coin ({}) does not match current coin ({})!'
			assert self.data['coin'] == g.coin,m.format(self.data['coin'],g.coin)
			if not 'tokens' in self.data:
				self.data['tokens'] = {}
			def conv_types(ad):
				for v in list(ad.values()):
					v['mmid'] = TwMMGenID(v['mmid'],on_fail='raise')
					v['comment'] = TwComment(v['comment'],on_fail='raise')
			conv_types(self.data['accounts'])
			for v in list(self.data['tokens'].values()):
				conv_types(v)

	def upgrade_wallet_maybe(self):
		if not 'accounts' in self.data or not 'coin' in self.data:
			ymsg('Upgrading {}!'.format(self.desc))
			if not 'accounts' in self.data:
				self.data = {}
				self.data['accounts'] = json.loads(self.orig_data)
			if not 'coin' in self.data:
				self.data['coin'] = g.coin
			mode_save = self.mode
			self.mode = 'w'
			self.write()
			self.mode = mode_save
			self.orig_data = json.dumps(self.data)
			msg('{} upgraded successfully!'.format(self.desc))

	def data_root(self): return self.data['accounts']
	def data_root_desc(self): return 'accounts'

	@write_mode
	def import_address(self,addr,label,foo):
		ad = self.data_root()
		if addr in ad:
			if not ad[addr]['mmid'] and label.mmid:
				msg("Warning: MMGen ID '{}' was missing in tracking wallet!".format(label.mmid))
			elif ad[addr]['mmid'] != label.mmid:
				die(3,"MMGen ID '{}' does not match tracking wallet!".format(label.mmid))
		ad[addr] = { 'mmid': label.mmid, 'comment': label.comment }

	@write_mode
	def write(self): # use 'check_data' to check wallet hasn't been altered by another program
		write_data_to_file( self.tw_file,
							json.dumps(self.data),'Ethereum tracking wallet data',
							ask_overwrite=False,ignore_opt_outdir=True,silent=True,
							check_data=True,cmp_data=self.orig_data)

	@write_mode
	def delete_all(self):
		self.data = {}
		self.write()

	@write_mode
	def remove_address(self,addr):
		root = self.data_root()

		from mmgen.obj import is_coin_addr,is_mmgen_id
		if is_coin_addr(addr):
			have_match = lambda k: k == addr
		elif is_mmgen_id(addr):
			have_match = lambda k: root[k]['mmid'] == addr
		else:
			die(1,"'{}' is not an Ethereum address or MMGen ID".format(addr))

		for k in root:
			if have_match(k):
				# return the addr resolved to mmid if possible
				ret = root[k]['mmid'] if is_mmgen_id(root[k]['mmid']) else addr
				del root[k]
				self.write()
				return ret
		else:
			m = "Address '{}' not found in '{}' section of tracking wallet"
			msg(m.format(addr,self.data_root_desc()))
			return None

	def is_in_wallet(self,addr):
		return addr in self.data_root()

	def sorted_list(self):
		return sorted(
			[{'addr':x[0],'mmid':x[1]['mmid'],'comment':x[1]['comment']} for x in list(self.data_root().items())],
			key=lambda x: x['mmid'].sort_key+x['addr'] )

	def mmid_ordered_dict(self):
		from collections import OrderedDict
		return OrderedDict([(x['mmid'],{'addr':x['addr'],'comment':x['comment']}) for x in self.sorted_list()])

	@write_mode
	def set_label(self,coinaddr,lbl):
		for addr,d in list(self.data_root().items()):
			if addr == coinaddr:
				d['comment'] = lbl.comment
				self.write()
				return None
		else: # emulate on_fail='return' of RPC library
			m = "Address '{}' not found in '{}' section of tracking wallet"
			return ('rpcfail',(None,2,m.format(coinaddr,self.data_root_desc())))

class EthereumTokenTrackingWallet(EthereumTrackingWallet):

	def token_is_in_wallet(self,addr):
		return addr in self.data['tokens']

	def data_root_desc(self):
		return 'token ' + Token(g.token).symbol()

	@write_mode
	def add_token(self,token):
		msg("Adding token '{}' to tracking wallet.".format(token))
		self.data['tokens'][token] = {}

	def data_root(self): # create the token data root if necessary
		if g.token not in self.data['tokens']:
			self.add_token(g.token)
		return self.data['tokens'][g.token]

	def sym2addr(self,sym): # online
		for addr in self.data['tokens']:
			if Token(addr).symbol().upper() == sym.upper():
				return addr
		return None

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
                 add [l]abel, [R]emove address:
"""
	key_mappings = {
		'a':'s_amt','d':'s_addr','r':'d_reverse','M':'s_twmmid',
		'm':'d_mmid','e':'d_redraw',
		'q':'a_quit','p':'a_print','v':'a_view','w':'a_view_wide',
		'l':'a_lbl_add','R':'a_addr_remove' }

	def do_sort(self,key=None,reverse=False):
		if key == 'txid': return
		super(EthereumTwUnspentOutputs,self).do_sort(key=key,reverse=reverse)

	def get_addr_bal(self,addr):
		return ETHAmt(int(g.rpch.eth_getBalance('0x'+addr),16),'wei')

	def get_unspent_rpc(self):
		rpc_init()
		return [{
				'account': TwLabel(d['mmid']+' '+d['comment'],on_fail='raise'),
				'address': d['addr'],
				'amount': self.get_addr_bal(d['addr']),
				'confirmations': 0, # TODO
				} for d in TrackingWallet().sorted_list()]

class EthereumTokenTwUnspentOutputs(EthereumTwUnspentOutputs):

	disp_type = 'token'
	prompt_fs = 'Total to spend: {} {}\n\n'
	col_adj = 37

	def get_display_precision(self): return 10 # truncate precision for narrow display

	def get_addr_bal(self,addr):
		return Token(g.token).balance(addr)

	def get_unspent_data(self):
		super(type(self),self).get_unspent_data()
		for e in self.unspent:
			e.amt2 = ETHAmt(int(g.rpch.eth_getBalance('0x'+e.addr),16),'wei')

class EthereumTwAddrList(TwAddrList):

	def __init__(self,usr_addr_list,minconf,showempty,showbtcaddrs,all_labels):

		rpc_init()
		if g.token: self.token = Token(g.token)

		tw = TrackingWallet().mmid_ordered_dict()
		self.total = g.proto.coin_amt('0')

		from mmgen.obj import CoinAddr
		for mmid,d in list(tw.items()):
#			if d['confirmations'] < minconf: continue # cannot get confirmations for eth account
			label = TwLabel(mmid+' '+d['comment'],on_fail='raise')
			if usr_addr_list and (label.mmid not in usr_addr_list): continue
			bal = self.get_addr_balance(d['addr'])
			if bal == 0 and not showempty:
				if not label.comment: continue
				if not all_labels: continue
			self[label.mmid] = {'amt': g.proto.coin_amt('0'), 'lbl':  label }
			if showbtcaddrs:
				self[label.mmid]['addr'] = CoinAddr(d['addr'])
			self[label.mmid]['lbl'].mmid.confs = None
			self[label.mmid]['amt'] += bal
			self.total += bal

	def get_addr_balance(self,addr):
		return ETHAmt(int(g.rpch.eth_getBalance('0x'+addr),16),'wei')

class EthereumTokenTwAddrList(EthereumTwAddrList):

	def get_addr_balance(self,addr):
		return self.token.balance(addr)

from mmgen.tw import TwGetBalance
class EthereumTwGetBalance(TwGetBalance):

	fs = '{w:13} {c}\n' # TODO - for now, just suppress display of meaningless data

	def create_data(self):
		data = TrackingWallet().mmid_ordered_dict()
		for d in data:
			if d.type == 'mmgen':
				key = d.obj.sid
				if key not in self.data:
					self.data[key] = [g.proto.coin_amt('0')] * 4
			else:
				key = 'Non-MMGen'

			conf_level = 2 # TODO
			amt = self.get_addr_balance(data[d]['addr'])

			self.data['TOTAL'][conf_level] += amt
			self.data[key][conf_level] += amt

	def get_addr_balance(self,addr):
		return ETHAmt(int(g.rpch.eth_getBalance('0x'+addr),16),'wei')

class EthereumTokenTwGetBalance(EthereumTwGetBalance):

	def get_addr_balance(self,addr):
		return Token(g.token).balance(addr)

class EthereumAddrData(AddrData):

	@classmethod
	def get_tw_data(cls):
		vmsg('Getting address data from tracking wallet')
		tw = TrackingWallet().mmid_ordered_dict()
		# emulate the output of RPC 'listaccounts' and 'getaddressesbyaccount'
		return [(mmid+' '+d['comment'],[d['addr']]) for mmid,d in list(tw.items())]

class EthereumTokenAddrData(EthereumAddrData): pass
