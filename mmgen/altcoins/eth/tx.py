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
altcoins.eth.tx: Ethereum transaction classes for the MMGen suite
"""

import json
from mmgen.common import *
from mmgen.obj import *

from mmgen.tx import MMGenTX,MMGenBumpTX,MMGenSplitTX,DeserializedTX,mmaddr2coinaddr
from mmgen.altcoins.eth.contract import Token

class EthereumMMGenTX(MMGenTX):
	desc   = 'Ethereum transaction'
	tx_gas = ETHAmt(21000,'wei')    # an approximate number, used for fee estimation purposes
	start_gas = ETHAmt(21000,'wei') # the actual startgas amt used in the transaction
									# for simple sends with no data, tx_gas = start_gas = 21000
	fee_fail_fs = 'Network fee estimation failed'
	no_chg_msg = 'Warning: Transaction leaves account with zero balance'
	rel_fee_desc = 'gas price'
	rel_fee_disp = 'gas price in Gwei'
	txview_hdr_fs = 'TRANSACTION DATA\n\nID={i} ({a} {c}) UTC={t} Sig={s} Locktime={l}\n'
	txview_hdr_fs_short = 'TX {i} ({a} {c}) UTC={t} Sig={s} Locktime={l}\n'
	txview_ftr_fs = 'Total in account: {i} {d}\nTotal to spend:   {o} {d}\nTX fee:           {a} {c}{r}\n'
	txview_ftr_fs_short = 'In {i} {d} - Out {o} {d}\nFee {a} {c}{r}\n'
	usr_fee_prompt = 'Enter transaction fee or gas price: '
	fn_fee_unit = 'Mwei'
	usr_rel_fee = None # not in MMGenTX
	disable_fee_check = False
	txobj  = None # ""
	data = HexBytes('')

	def __init__(self,*args,**kwargs):
		super(EthereumMMGenTX,self).__init__(*args,**kwargs)
		if hasattr(opt,'tx_gas') and opt.tx_gas:
			self.tx_gas = self.start_gas = ETHAmt(int(opt.tx_gas),'wei')
		if hasattr(opt,'contract_data') and opt.contract_data:
			m = "'--contract-data' option may not be used with token transaction"
			assert not 'Token' in type(self).__name__, m
			self.data = HexBytes(open(opt.contract_data).read().strip())
			self.disable_fee_check = True

	@classmethod
	def get_receipt(cls,txid):
		return g.rpch.eth_getTransactionReceipt('0x'+txid.decode())

	@classmethod
	def get_exec_status(cls,txid,silent=False):
		d = g.rpch.eth_getTransactionReceipt('0x'+txid.decode())
		if not silent:
			if 'contractAddress' in d and d['contractAddress']:
				msg('Contract address: {}'.format(d['contractAddress'].replace('0x','')))
		return int(d['status'],16)

	def is_replaceable(self): return True

	def get_fee_from_tx(self):
		return self.fee

	def check_fee(self):
		if self.disable_fee_check: return
		assert self.fee <= g.proto.max_tx_fee

	def get_hex_locktime(self): return None # TODO

	def check_pubkey_scripts(self): pass

	def check_sigs(self,deserial_tx=None):
		if is_hex_bytes(self.hex):
			self.mark_signed()
			return True
		return False

	# hex data if signed, json if unsigned: see create_raw()
	def check_txfile_hex_data(self):
		if type(self.hex) == str: self.hex = self.hex.encode()
		if self.check_sigs():
			from ethereum.transactions import Transaction
			import rlp
			etx = rlp.decode(unhexlify(self.hex),Transaction)
			d = etx.to_dict() # ==> hex values have '0x' prefix, 0 is '0x'
			for k in ('sender','to','data'):
				if k in d: d[k] = d[k].replace('0x','',1)
			o = {   'from':     CoinAddr(d['sender']),
					'to':       CoinAddr(d['to']) if d['to'] else Str(''),
					'amt':      ETHAmt(d['value'],'wei'),
					'gasPrice': ETHAmt(d['gasprice'],'wei'),
					'startGas': ETHAmt(d['startgas'],'wei'),
					'nonce':    ETHNonce(d['nonce']),
					'data':     HexBytes(d['data']) }
			if o['data'] and not o['to']:
				self.token_addr = TokenAddr(hexlify(etx.creates).decode())
			txid = CoinTxID(hexlify(etx.hash))
			assert txid == self.coin_txid,"txid in tx.hex doesn't match value in MMGen transaction file"
		else:
			d = json.loads(self.hex)
			o = {   'from':     CoinAddr(d['from']),
					'to':       CoinAddr(d['to']) if d['to'] else Str(''),
					'amt':      ETHAmt(d['amt']),
					'gasPrice': ETHAmt(d['gasPrice']),
					'startGas': ETHAmt(d['startGas']),
					'nonce':    ETHNonce(d['nonce']),
					'chainId':  Int(d['chainId']),
					'data':     HexBytes(d['data']) }
		self.tx_gas = o['startGas'] # approximate, but better than nothing
		self.data = o['data']
		if o['data'] and not o['to']: self.disable_fee_check = True
		self.fee = self.fee_rel2abs(o['gasPrice'].toWei())
		self.txobj = o
		return d # 'token_addr','decimals' required by subclass

	def get_nonce(self):
		return ETHNonce(int(g.rpch.parity_nextNonce('0x'+self.inputs[0].addr),16))

	def make_txobj(self): # create_raw
		self.txobj = {
			'from': self.inputs[0].addr,
			'to':   self.outputs[0].addr if self.outputs else Str(''),
			'amt':  self.outputs[0].amt if self.outputs else ETHAmt('0'),
			'gasPrice': self.usr_rel_fee or self.fee_abs2rel(self.fee,to_unit='eth'),
			'startGas': self.start_gas,
			'nonce': self.get_nonce(),
			'chainId': Int(g.rpch.parity_chainId(),16),
			'data':  self.data,
		}

	# Instead of serializing tx data as with BTC, just create a JSON dump.
	# This complicates things but means we avoid using the rlp library to deserialize the data,
	# thus removing an attack vector
	def create_raw(self):
		assert len(self.inputs) == 1,'Transaction has more than one input!'
		o_ok = (0,1) if self.data else (1,)
		o_num = len(self.outputs)
		assert o_num in o_ok,'Transaction has invalid number of outputs!'.format(o_num)
		self.make_txobj()
		self.hex = json.dumps(dict([(k,str(v))for k,v in list(self.txobj.items())]))
		self.update_txid()

	def del_output(self,idx): pass

	def update_txid(self):
		assert not is_hex_str(self.hex),'update_txid() must be called only when self.hex is not hex data'
		self.txid = MMGenTxID(make_chksum_6(self.hex).upper())

	def get_blockcount(self):
		return Int(g.rpch.eth_blockNumber(),16)

	def process_cmd_args(self,cmd_args,ad_f,ad_w):
		lc = len(cmd_args)
		if lc == 0 and self.data and not 'Token' in type(self).__name__: return
		if lc != 1:
			fs = '{} output{} specified, but Ethereum transactions must have exactly one'
			die(1,fs.format(lc,suf(lc)))

		for a in cmd_args: self.process_cmd_arg(a,ad_f,ad_w)

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
	def get_relay_fee(self): return ETHAmt('0') # TODO

	# given absolute fee in ETH, return gas price in Gwei using tx_gas
	def fee_abs2rel(self,abs_fee,to_unit='Gwei'):
		ret = ETHAmt(int(abs_fee.toWei() // self.tx_gas.toWei()),'wei')
		dmsg('fee_abs2rel() ==> {} ETH'.format(ret))
		return ret if to_unit == 'eth' else ret.to_unit(to_unit,show_decimal=True)

	# get rel_fee (gas price) from network, return in native wei
	def get_rel_fee_from_network(self):
		return Int(g.rpch.eth_gasPrice(),16),'eth_gasPrice' # ==> rel_fee,fe_type

	# given rel fee and units, return absolute fee using tx_gas
	def convert_fee_spec(self,foo,units,amt,unit):
		self.usr_rel_fee = ETHAmt(int(amt),units[unit])
		return ETHAmt(self.usr_rel_fee.toWei() * self.tx_gas.toWei(),'wei')

	# given rel fee in wei, return absolute fee using tx_gas (not in MMGenTX)
	def fee_rel2abs(self,rel_fee):
		assert type(rel_fee) in (int,Int),"'{}': incorrect type for fee estimate (not an integer)".format(rel_fee)
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
		elif self.disable_fee_check:
			return abs_fee
		elif abs_fee > g.proto.max_tx_fee:
			m = '{} {c}: {} fee too large (maximum fee: {} {c})'
			msg(m.format(abs_fee.hl(),desc,g.proto.max_tx_fee.hl(),c=g.coin))
			return False
		else:
			return abs_fee

	def update_change_output(self,change_amt):
		if self.outputs and self.outputs[0].is_chg:
			self.update_output_amt(0,ETHAmt(change_amt))

	def update_send_amt(self,foo):
		if self.outputs:
			self.send_amt = self.outputs[0].amt

	def format_view_body(self,blockcount,nonmm_str,max_mmwid,enl,terse):
		m = {}
		for k in ('in','out'):
			if len(getattr(self,k+'puts')):
				m[k] = getattr(self,k+'puts')[0].mmid if len(getattr(self,k+'puts')) else ''
				m[k] = ' ' + m[k].hl() if m[k] else ' ' + MMGenID.hlc(nonmm_str)
		fs = """From:      {}{f_mmid}
				To:        {}{t_mmid}
				Amount:    {} {c}
				Gas price: {g} Gwei
				Start gas: {G} Kwei
				Nonce:     {}
				Data:      {d}
				\n""".replace('\t','')
		keys = ('from','to','amt','nonce')
		ld = len(self.txobj['data'])
		return fs.format(   *((self.txobj[k] if self.txobj[k] != '' else Str('None')).hl() for k in keys),
							d='{}... ({} bytes)'.format(self.txobj['data'][:40],ld//2) if ld else Str('None'),
							c=g.dcoin if len(self.outputs) else '',
							g=yellow(str(self.txobj['gasPrice'].to_unit('Gwei',show_decimal=True))),
							G=yellow(str(self.txobj['startGas'].toKwei())),
							t_mmid=m['out'] if len(self.outputs) else '',
							f_mmid=m['in'])

	def format_view_abs_fee(self):
		fee = self.fee_rel2abs(self.txobj['gasPrice'].toWei())
		note = ' (max)' if self.data else ''
		return fee.hl() + note

	def format_view_rel_fee(self,terse): return ''
	def format_view_verbose_footer(self): return '' # TODO

	def set_g_token(self):
		die(2,"Transaction object mismatch.  Have you forgotten to include the '--token' option?")

	def final_inputs_ok_msg(self,change_amt):
		m = "Transaction leaves {} {} in the sender's account"
		chg = '0' if (self.outputs and self.outputs[0].is_chg) else change_amt
		return m.format(ETHAmt(chg).hl(),g.coin)

	def do_sign(self,d,wif,tx_num_str):

		d_in = {'to':       unhexlify(d['to']),
				'startgas': d['startGas'].toWei(),
				'gasprice': d['gasPrice'].toWei(),
				'value':    d['amt'].toWei() if d['amt'] else 0,
				'nonce':    d['nonce'],
				'data':     unhexlify(d['data'])}

		msg_r('Signing transaction{}...'.format(tx_num_str))

		try:
			from ethereum.transactions import Transaction
			etx = Transaction(**d_in)
			etx.sign(wif,d['chainId'])
			import rlp
			self.hex = hexlify(rlp.encode(etx))
			self.coin_txid = CoinTxID(hexlify(etx.hash))
			msg('OK')
			if d['data']:
				self.token_addr = TokenAddr(hexlify(etx.creates))
		except Exception as e:
			m = "{!r}: transaction signing failed!"
			msg(m.format(e.args[0]))
			return False

		return self.check_sigs()

	def sign(self,tx_num_str,keys): # return True or False; don't exit or raise exception

		if self.marked_signed():
			msg('Transaction is already signed!')
			return False

		if not self.check_correct_chain(on_fail='return'):
			return False

		return self.do_sign(self.txobj,keys[0].sec.wif,tx_num_str)

	def is_in_mempool(self):
#		pmsg(g.rpch.parity_pendingTransactions())
		return '0x'+self.coin_txid.decode() in [x['hash'] for x in g.rpch.parity_pendingTransactions()]

	def is_in_wallet(self):
		d = g.rpch.eth_getTransactionReceipt('0x'+self.coin_txid.decode())
		if d and 'blockNumber' in d and d['blockNumber'] is not None:
			return 1 + int(g.rpch.eth_blockNumber(),16) - int(d['blockNumber'],16)
		return False

	def get_status(self,status=False):
		if self.is_in_mempool():
			msg('Transaction is in mempool' if status else 'Warning: transaction is in mempool!')
			return

		confs = self.is_in_wallet()
		if confs is not False:
			if self.data:
				exec_status = type(self).get_exec_status(self.coin_txid)
				if exec_status == 0:
					msg('Contract failed to execute!')
				else:
					msg('Contract successfully executed with status {}'.format(exec_status))
			die(0,'Transaction has {} confirmation{}'.format(confs,suf(confs,'s')))

		if status:
			die(1,'Transaction is neither in mempool nor blockchain!')

	def send(self,prompt_user=True,exit_on_fail=False):

		if not self.marked_signed():
			die(1,'Transaction is not signed!')

		self.check_correct_chain(on_fail='die')

		bogus_send = os.getenv('MMGEN_BOGUS_SEND')

		fee = self.fee_rel2abs(self.txobj['gasPrice'].toWei())

		if not self.disable_fee_check and fee > g.proto.max_tx_fee:
			die(2,'Transaction fee ({}) greater than {} max_tx_fee ({} {})!'.format(
				fee,g.proto.name.capitalize(),g.proto.max_tx_fee,g.coin))

		self.get_status()

		if prompt_user: self.confirm_send()

		ret = None if bogus_send else g.rpch.eth_sendRawTransaction('0x'+self.hex.decode(),on_fail='return')

		from mmgen.rpc import rpc_error,rpc_errmsg
		if rpc_error(ret):
			msg(yellow(rpc_errmsg(ret)))
			msg(red('Send of MMGen transaction {} failed'.format(self.txid)))
			if exit_on_fail: sys.exit(1)
			return False
		else:
			m = 'BOGUS transaction NOT sent: {}' if bogus_send else 'Transaction sent: {}'
			if not bogus_send:
				assert ret == '0x'+self.coin_txid.decode(),'txid mismatch (after sending)'
			self.desc = 'sent transaction'
			msg(m.format(self.coin_txid.hl()))
			self.add_timestamp()
			self.add_blockcount()
			return True

class EthereumTokenMMGenTX(EthereumMMGenTX):
	desc   = 'Ethereum token transaction'
	tx_gas = ETHAmt(52000,'wei')
	start_gas = ETHAmt(60000,'wei')
	fee_is_approximate = True

	def update_change_output(self,change_amt):
		if self.outputs[0].is_chg:
			self.update_output_amt(0,self.inputs[0].amt)

	def check_sufficient_funds(self,inputs_sum,sel_unspent):
		eth_bal = ETHAmt(int(g.rpch.eth_getBalance('0x'+sel_unspent[0].addr),16),'wei')
		if eth_bal == 0: # we don't know the fee yet
			msg('This account has no ether to pay for the transaction fee!')
			return False
		if self.send_amt > inputs_sum:
			msg(self.msg_low_coin.format(self.send_amt-inputs_sum,g.dcoin))
			return False
		return True

	def final_inputs_ok_msg(self,change_amt):
		m = "Transaction leaves ≈{} {} and {} {} in the sender's account"
		send_acct_tbal = '0' if self.outputs[0].is_chg else \
				Token(g.token).balance(self.inputs[0].addr) - self.outputs[0].amt
		return m.format(ETHAmt(change_amt).hl(),g.coin,ETHAmt(send_acct_tbal).hl(),g.dcoin)

	def get_change_amt(self): # here we know the fee
		eth_bal = ETHAmt(int(g.rpch.eth_getBalance('0x'+self.inputs[0].addr),16),'wei')
		return eth_bal - self.fee

	def set_g_token(self):
		g.dcoin = self.dcoin
		if is_hex_bytes(self.hex): return # for txsend we can leave g.token uninitialized
		d = json.loads(self.hex)
		if g.token.upper() == self.dcoin:
			g.token = d['token_addr']
		elif g.token != d['token_addr']:
			m1 = "'{p}': invalid --token parameter for {t} Ethereum token transaction file\n"
			m2 = "Please use '--token={t}'"
			die(1,(m1+m2).format(p=g.token,t=self.dcoin))

	def make_txobj(self):
		super(EthereumTokenMMGenTX,self).make_txobj()
		t = Token(g.token)
		o = t.txcreate( self.inputs[0].addr,
						self.outputs[0].addr,
						(self.inputs[0].amt if self.outputs[0].is_chg else self.outputs[0].amt),
						self.start_gas,
						self.usr_rel_fee or self.fee_abs2rel(self.fee,to_unit='eth'))
		self.txobj['token_addr'] = self.token_addr = t.addr
		self.txobj['decimals']   = t.decimals()

	def check_txfile_hex_data(self):
		d = super(EthereumTokenMMGenTX,self).check_txfile_hex_data()
		o = self.txobj
		if self.check_sigs(): # online, from rlp
			rpc_init()
			o['token_addr'] = TokenAddr(o['to'])
			o['amt']        = Token(o['token_addr']).transferdata2amt(o['data'])
		else:                # offline, from json
			o['token_addr'] = TokenAddr(d['token_addr'])
			o['decimals']   = Int(d['decimals'])
			t = Token(o['token_addr'],o['decimals'])
			self.data = o['data'] = t.create_data(o['to'],o['amt'])

	def format_view_body(self,*args,**kwargs):
		return 'Token:     {d} {c}\n{r}'.format(
			d=self.txobj['token_addr'].hl(),
			c=blue('(' + g.dcoin + ')'),
			r=super(EthereumTokenMMGenTX,self).format_view_body(*args,**kwargs))

	def do_sign(self,d,wif,tx_num_str):
		d = self.txobj
		msg_r('Signing transaction{}...'.format(tx_num_str))
		try:
			t = Token(d['token_addr'],decimals=d['decimals'])
			tx_in = t.txcreate(d['from'],d['to'],d['amt'],self.start_gas,d['gasPrice'],nonce=d['nonce'])
			(self.hex,self.coin_txid) = t.txsign(tx_in,wif,d['from'],chain_id=d['chainId'])
			msg('OK')
		except Exception as e:
			m = "{!r}: transaction signing failed!"
			msg(m.format(e.args[0]))
			return False

		return self.check_sigs()

class EthereumMMGenBumpTX(EthereumMMGenTX,MMGenBumpTX):

	def choose_output(self): pass

	def set_min_fee(self):
		self.min_fee = ETHAmt(self.fee * Decimal('1.101'))

	def update_fee(self,foo,fee):
		self.fee = fee

	def get_nonce(self):
		return self.txobj['nonce']

class EthereumTokenMMGenBumpTX(EthereumTokenMMGenTX,EthereumMMGenBumpTX): pass

class EthereumMMGenSplitTX(MMGenSplitTX): pass
class EthereumDeserializedTX(DeserializedTX): pass
