#!/usr/bin/env python
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
altcoins.eth.tx: Ethereum transaction routines for the MMGen suite
"""

import json
from mmgen.common import *
from mmgen.obj import *

from mmgen.tx import MMGenTX,MMGenBumpTX,MMGenSplitTX,DeserializedTX,mmaddr2coinaddr
class EthereumMMGenTX(MMGenTX):
	desc   = 'Ethereum transaction'
	tx_gas = ETHAmt(21000,'wei') # tx_gas 21000 * gasPrice 50 Gwei = fee 0.00105
	chg_msg_fs = 'Transaction leaves {} {} in the account'
	fee_fail_fs = 'Network fee estimation failed'
	no_chg_msg = 'Warning: Transaction leaves account with zero balance'
	rel_fee_desc = 'gas price'
	rel_fee_disp = 'gas price in Gwei'
	txview_hdr_fs = 'TRANSACTION DATA\n\nID={i} ({a} {c}) UTC={t} Sig={s} Locktime={l}\n'
	txview_hdr_fs_short = 'TX {i} ({a} {c}) UTC={t} Sig={s} Locktime={l}\n'
	usr_fee_prompt = 'Enter transaction fee or gas price: '

	usr_rel_fee = None # not in MMGenTX
	txobj_data  = None # ""

	def check_fee(self):
		assert self.fee <= g.proto.max_tx_fee

	def get_hex_locktime(self): return None # TODO

	def check_pubkey_scripts(self): pass

	def check_sigs(self,deserial_tx=None):
		if is_hex_str(self.hex):
			self.mark_signed()
			return True
		return False

	# hex data if signed, json if unsigned
	def check_tx_hex_data(self):
		if self.check_sigs():
			from ethereum.transactions import Transaction
			import rlp
			etx = rlp.decode(self.hex.decode('hex'),Transaction)
			d = etx.to_dict()
			self.txobj_data = {
				'from':     CoinAddr(d['sender'][2:]),
				'to':       CoinAddr(d['to'][2:]),
				'amt':      ETHAmt(d['value'],'wei'),
				'gasPrice': ETHAmt(d['gasprice'],'wei'),
				'nonce':    ETHNonce(d['nonce'])
			}
			txid = CoinTxID(etx.hash.encode('hex'))
			assert txid == self.coin_txid,"txid in tx.hex doesn't match value in MMGen tx file"
		else:
			d = json.loads(self.hex)
			self.txobj_data = {
				'from':     CoinAddr(d['from']),
				'to':       CoinAddr(d['to']),
				'amt':      ETHAmt(d['amt']),
				'gasPrice': ETHAmt(d['gasPrice']),
				'nonce':    ETHNonce(d['nonce']),
				'chainId':  d['chainId']
			}
		self.gasPrice = self.txobj_data['gasPrice']

	def create_raw(self):
		for k in 'input','output':
			assert len(getattr(self,k+'s')) == 1,'Transaction has more than one {}!'.format(k)
		self.txobj_data = {
			'from': self.inputs[0].addr,
			'to':   self.outputs[0].addr,
			'amt':  self.outputs[0].amt,
			'gasPrice': self.usr_rel_fee or self.fee_abs2rel(self.fee,in_eth=True),
			'nonce': ETHNonce(int(g.rpch.parity_nextNonce('0x'+self.inputs[0].addr),16)),
			'chainId': g.rpch.parity_chainId()
		}
		self.hex = json.dumps(dict([(k,str(v))for k,v in self.txobj_data.items()]))
		self.update_txid()

	def del_output(self,idx): pass
	def update_output_amt(self,idx,amt): pass
	def get_chg_output_idx(self): return None

	def update_txid(self):
		assert not is_hex_str(self.hex),'update_txid() must be called only when self.hex is not hex data'
		self.txid = MMGenTxID(make_chksum_6(self.hex).upper())

	def get_blockcount(self):
		return int(g.rpch.eth_blockNumber(),16)

	def process_cmd_args(self,cmd_args,ad_f,ad_w):
		lc = len(cmd_args)
		if lc != 1:
			fs = '{} output{} specified, but Ethereum transactions must have only one'
			die(1,fs.format(lc,suf(lc)))

		a = list(cmd_args)[0]
		if ',' in a:
			a1,a2 = a.split(',',1)
			if is_mmgen_id(a1) or is_coin_addr(a1):
				coin_addr = mmaddr2coinaddr(a1,ad_w,ad_f) if is_mmgen_id(a1) else CoinAddr(a1)
				self.add_output(coin_addr,ETHAmt(a2))
			else:
				die(2,"{}: invalid subargument in command-line argument '{}'".format(a1,a))
		else:
			die(2,'{}: invalid command-line argument'.format(a))

	def select_unspent(self,unspent):
		prompt = 'Enter an account to spend from: '
		while True:
			reply = my_raw_input(prompt).strip()
			if reply:
				if not is_int(reply):
					msg('Account number must be an integer')
				elif int(reply) < 1:
					msg('Account number must be >= 1')
				elif int(reply) > len(unspent):
					msg('Account number must be <= {}'.format(len(unspent)))
				else:
					return [int(reply)]

	# coin-specific fee routines:
	def get_relay_fee(self): return ETHAmt(0) # TODO

	# given absolute fee in ETH, return gas price in Gwei using tx_gas
	def fee_abs2rel(self,abs_fee,in_eth=False): # in_eth not in MMGenTX
		ret = ETHAmt(int(abs_fee.toWei() / self.tx_gas.toWei()),'wei')
		return ret if in_eth else ret.toGwei()

	# get rel_fee (gas price) from network, return in native wei
	def get_rel_fee_from_network(self):
		return int(g.rpch.eth_gasPrice(),16),'eth_gasPrice' # ==> rel_fee,fe_type

	# given rel fee and units, return absolute fee using tx_gas
	def convert_fee_spec(self,foo,units,amt,unit):
		self.usr_rel_fee = ETHAmt(int(amt),units[unit])
		return ETHAmt(self.usr_rel_fee.toWei() * self.tx_gas.toWei(),'wei')

	# given rel fee in wei, return absolute fee using tx_gas (not in MMGenTX)
	def fee_rel2abs(self,rel_fee):
		assert type(rel_fee) is int,"'{}': incorrect type for fee estimate (not an integer)".format(rel_fee)
		return ETHAmt(rel_fee * self.tx_gas.toWei(),'wei')

	# given fee estimate (gas price) in wei, return absolute fee, adjusting by opt.tx_fee_adj
	def fee_est2abs(self,rel_fee,fe_type=None):
		ret = self.fee_rel2abs(rel_fee) * opt.tx_fee_adj
		if opt.verbose:
			msg('Estimated fee: {} ETH'.format(ret))
		return ret

	def convert_and_check_fee(self,tx_fee,desc='Missing description'):
		abs_fee = self.process_fee_spec(tx_fee,None,on_fail='return')
		if abs_fee == False:
			return False
		elif abs_fee > g.proto.max_tx_fee:
			m = '{} {c}: {} fee too large (maximum fee: {} {c})'
			msg(m.format(abs_fee.hl(),desc,g.proto.max_tx_fee.hl(),c=g.coin))
			return False
		else:
			return abs_fee

	def format_view_body(self,blockcount,nonmm_str,max_mmwid,enl,terse):
		m = {}
		for k in ('in','out'):
			m[k] = getattr(self,k+'puts')[0].mmid
			m[k] = ' ' + m[k].hl() if m[k] else ' ' + MMGenID.hlc(nonmm_str)
		fs = """From:      {}{f_mmid}
				To:        {}{t_mmid}
				Amount:    {} ETH
				Gas price: {g} Gwei
				Nonce:     {}\n\n""".replace('\t','')
		keys = ('from','to','amt','nonce')
		return fs.format(   *(self.txobj_data[k].hl() for k in keys),
							g=yellow(str(self.txobj_data['gasPrice'].toGwei())),
							t_mmid=m['out'],
							f_mmid=m['in'])

	def format_view_abs_fee(self):
		return self.fee_rel2abs(self.txobj_data['gasPrice'].toWei()).hl()

	def format_view_rel_fee(self,terse): return ''
	def format_view_verbose_footer(self): return '' # TODO

	def sign(self,tx_num_str,keys): # return true or false; don't exit

		if self.marked_signed():
			msg('Transaction is already signed!')
			return False

		if not self.check_correct_chain(on_fail='return'):
			return False

		wif = keys[0].sec.wif
		d = self.txobj_data

		out = { 'to':       '0x'+d['to'],
				'startgas': self.tx_gas.toWei(),
				'gasprice': d['gasPrice'].toWei(),
				'value':    d['amt'].toWei(),
				'nonce':    d['nonce'],
				'data':     ''}

		msg_r('Signing transaction{}...'.format(tx_num_str))

		try:
			from ethereum.transactions import Transaction
			etx = Transaction(**out)
			etx.sign(wif,int(d['chainId'],16))
			import rlp
			self.hex = rlp.encode(etx).encode('hex')
			self.coin_txid = CoinTxID(etx.hash.encode('hex'))
			msg('OK')
		except Exception as e:
			m = "{!r}: transaction signing failed!"
			msg(m.format(e[0]))
			return False

		return self.check_sigs()

	def get_status(self,status=False): pass # TODO

	def send(self,prompt_user=True,exit_on_fail=False):

		if not self.marked_signed():
			die(1,'Transaction is not signed!')

		self.check_correct_chain(on_fail='die')

		bogus_send = os.getenv('MMGEN_BOGUS_SEND')

		fee = self.fee_rel2abs(self.txobj_data['gasPrice'].toWei())

		if fee > g.proto.max_tx_fee:
			die(2,'Transaction fee ({}) greater than {} max_tx_fee ({} {})!'.format(
				fee,g.proto.name.capitalize(),g.proto.max_tx_fee,g.coin))

		self.get_status()

		if prompt_user: self.confirm_send()

		ret = None if bogus_send else g.rpch.eth_sendRawTransaction('0x'+self.hex,on_fail='return')

		from mmgen.rpc import rpc_error,rpc_errmsg
		if rpc_error(ret):
			msg(yellow(rpc_errmsg(ret)))
			msg(red('Send of MMGen transaction {} failed'.format(self.txid)))
			if exit_on_fail: sys.exit(1)
			return False
		else:
			m = 'BOGUS transaction NOT sent: {}' if bogus_send else 'Transaction sent: {}'
			if not bogus_send:
				assert ret == '0x'+self.coin_txid,'txid mismatch (after sending)'
			self.desc = 'sent transaction'
			msg(m.format(self.coin_txid.hl()))
			self.add_timestamp()
			self.add_blockcount()
			return True

class EthereumMMGenBumpTX(MMGenBumpTX): pass
class EthereumMMGenSplitTX(MMGenSplitTX): pass
class EthereumDeserializedTX(DeserializedTX): pass
