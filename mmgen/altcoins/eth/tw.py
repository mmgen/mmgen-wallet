#!/usr/bin/env python
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
altcoins.eth.tw: ETH tracking wallet functions and methods for the MMGen suite
"""

import json
from mmgen.common import *
from mmgen.obj import ETHAmt,TwMMGenID,TwComment,TwLabel
from mmgen.tw import TrackingWallet,TwAddrList,TwUnspentOutputs
from mmgen.addr import AddrData

# No file locking - 2 processes accessing the wallet at the same time will corrupt it
class EthereumTrackingWallet(TrackingWallet):

	data_dir = os.path.join(g.altcoin_data_dir,'eth',g.proto.data_subdir)
	tw_file = os.path.join(data_dir,'tracking-wallet.json')

	def __init__(self):
		check_or_create_dir(self.data_dir)
		try:
			self.data = json.loads(get_data_from_file(self.tw_file,silent=True))
		except:
			try: os.stat(self.tw_file)
			except: self.data = {}
			else: die(2,"File '{}' exists but does not contain valid json data")
		else:
			for d in self.data:
				self.data[d]['mmid'] = TwMMGenID(self.data[d]['mmid'],on_fail='raise')
				self.data[d]['comment'] = TwComment(self.data[d]['comment'],on_fail='raise')

	def import_address(self,addr,label):
		if addr in self.data:
			if not self.data[addr]['mmid'] and label.mmid:
				msg("Warning: MMGen ID '{}' was missing in tracking wallet!".format(label.mmid))
			elif self.data[addr]['mmid'] != label.mmid:
				die(3,"MMGen ID '{}' does not match tracking wallet!".format(label.mmid))
		self.data[addr] = { 'mmid': label.mmid, 'comment': label.comment }

	def write(self):
		write_data_to_file(
			self.tw_file,
			json.dumps(self.data),
			'Ethereum address data',
			ask_overwrite=False,
			silent=True)

	def delete_all(self):
		self.data = {}
		self.write()

	def delete(self,addr):
		if is_coin_addr(addr):
			have_match = lambda k: k == addr
		elif is_mmgen_id(addr):
			have_match = lambda k: self.data[k]['mmid'] == addr
		else:
			die(1,"'{}' is not an Ethereum address or MMGen ID".format(addr))

		for k in self.data:
			if have_match(k):
				del self.data[k]
				break
		else:
			die(1,"Address '{}' not found in tracking wallet".format(addr))
		self.write()

	def sorted_list(self):
		return sorted(
			map(lambda x: {'addr':x[0], 'mmid':x[1]['mmid'], 'comment':x[1]['comment'] }, self.data.items()),
			key=lambda x: x['mmid'].sort_key+x['addr']
			)

	def mmid_ordered_dict(self):
		from collections import OrderedDict
		return OrderedDict(map(lambda x: (x['mmid'],{'addr':x['addr'],'comment':x['comment']}), self.sorted_list()))

	def import_label(self,coinaddr,lbl):
		for addr,d in self.data.items():
			if addr == coinaddr:
				d['comment'] = lbl.comment
				self.write()
				return None
		else: # emulate RPC library
			return ('rpcfail',(None,2,"Address '{}' not found in tracking wallet".format(coinaddr)))

# Use consistent naming, even though Ethereum doesn't have unspent outputs
class EthereumTwUnspentOutputs(TwUnspentOutputs):

	show_txid = False
	can_group = False
	hdr_fmt = 'TRACKED ACCOUNTS (sort order: {})\nTotal {}: {}'
	desc    = 'account balances'
	dump_fn_pfx = 'balances'
	prompt = """
Sort options: [a]mount, a[d]dress, [A]ge, [r]everse, [M]mgen addr
Display options: show [D]ays, show [m]mgen addr, r[e]draw screen
"""

	def do_sort(self,key=None,reverse=False):
		if key == 'txid': return
		super(type(self),self).do_sort(key=key,reverse=reverse)

	def get_unspent_rpc(self):
		rpc_init()
		return map(lambda d: {
				'account': TwLabel(d['mmid']+' '+d['comment'],on_fail='raise'),
				'address': d['addr'],
				'amount': ETHAmt(int(g.rpch.eth_getBalance('0x'+d['addr']),16),'wei'),
				'confirmations': 0, # TODO
				}, EthereumTrackingWallet().sorted_list())

class EthereumTwAddrList(TwAddrList):

	def __init__(self,usr_addr_list,minconf,showempty,showbtcaddrs,all_labels):
		tw = EthereumTrackingWallet().mmid_ordered_dict()
		self.total = g.proto.coin_amt('0')

		rpc_init()
#		cur_blk = int(g.rpch.eth_blockNumber(),16)

		from mmgen.obj import CoinAddr
		for mmid,d in tw.items():
#			if d['confirmations'] < minconf: continue
			label = TwLabel(mmid+' '+d['comment'],on_fail='raise')
			if usr_addr_list and (label.mmid not in usr_addr_list): continue
			bal = ETHAmt(int(g.rpch.eth_getBalance('0x'+d['addr']),16),'wei')
			if bal == 0 and not showempty:
				if not label.comment: continue
				if not all_labels: continue
			self[label.mmid] = {'amt': g.proto.coin_amt('0'), 'lbl':  label }
			if showbtcaddrs:
				self[label.mmid]['addr'] = CoinAddr(d['addr'])
			self[label.mmid]['lbl'].mmid.confs = 9999 # TODO
			self[label.mmid]['amt'] += bal
			self.total += bal

class EthereumAddrData(AddrData):

	@classmethod
	def get_tw_data(cls):
		vmsg('Getting address data from tracking wallet')
		tw = EthereumTrackingWallet().mmid_ordered_dict()
		# emulate the output of RPC 'listaccounts' and 'getaddressesbyaccount'
		return [(mmid+' '+d['comment'],[d['addr']]) for mmid,d in tw.items()]
